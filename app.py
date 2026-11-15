import os
import uuid
import io
import math
import queue
import re
import hmac
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory, session, Response
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image, UnidentifiedImageError

import database as db
import migrate_complaints
from email_notifications import email_is_configured, send_email
import events
from sms_notifications import send_sms, sms_is_configured
from text_classifier import CATEGORIES as TEXT_CATEGORIES
from priority import score_priority, effective_priority

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get(
    "CITYSOLUTION_UPLOAD_DIR", os.path.join(BASE_DIR, "static", "uploads")
)
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
IS_PRODUCTION = os.environ.get("CITYSOLUTION_ENV", "").lower() == "production"
PRESENTATION_MODE = (
    os.environ.get("CITYSOLUTION_PRESENTATION_MODE", "").casefold() == "true"
)
if PRESENTATION_MODE and (IS_PRODUCTION or db.USE_POSTGRES):
    raise RuntimeError(
        "CITYSOLUTION_PRESENTATION_MODE is only allowed with a local SQLite database."
    )
if IS_PRODUCTION:
    required_settings = (
        "CITYSOLUTION_SECRET_KEY",
        "CITYSOLUTION_AUTHORITY_USERNAME",
        "CITYSOLUTION_AUTHORITY_PASSWORD",
        "DATABASE_URL",
    )
    missing_settings = [
        name for name in required_settings
        if not os.environ.get(name, "").strip()
    ]
    if missing_settings:
        raise RuntimeError(
            "Missing production settings: " + ", ".join(missing_settings)
        )

app.secret_key = os.environ.get("CITYSOLUTION_SECRET_KEY", "dev-secret-key-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["CITYSOLUTION_ENABLE_MIGRATION"] = (
    os.environ.get("CITYSOLUTION_ENABLE_MIGRATION", "").casefold() == "true"
)
app.config["CITYSOLUTION_ENABLE_SAMPLE_IMPORT"] = (
    os.environ.get("CITYSOLUTION_ENABLE_SAMPLE_IMPORT", "").casefold() == "true"
)
app.config["CITYSOLUTION_PUBLIC_SAMPLE_DATA"] = (
    os.environ.get("CITYSOLUTION_PUBLIC_SAMPLE_DATA", "").casefold() == "true"
)
app.config["CITYSOLUTION_PRESENTATION_MODE"] = PRESENTATION_MODE
AUTHORITY_USERNAME = os.environ.get("CITYSOLUTION_AUTHORITY_USERNAME", "admin")
AUTHORITY_PASSWORD = os.environ.get("CITYSOLUTION_AUTHORITY_PASSWORD", "admin12")


@app.template_filter("complaint_image_url")
def complaint_image_url(image_path):
    if image_path.startswith("uploads/"):
        return url_for("uploaded_file", filename=image_path[len("uploads/"):])
    return url_for("static", filename=image_path)

CITIES = [
    "Koramangala", "Indiranagar", "Whitefield", "HSR Layout", "Jayanagar",
    "Malleswaram", "Rajajinagar", "BTM Layout", "Marathahalli", "Yelahanka",
    "Basavanagudi", "JP Nagar", "Hebbal", "Electronic City", "Banashankari",
    "RT Nagar", "Vijayanagar", "Sarjapur Road", "Bellandur", "KR Puram",
]
ALL_CATEGORIES = sorted(set(TEXT_CATEGORIES))
COMPLAINT_LANGUAGES = {
    "en": ("English", "en-US"),
    "kn": ("ಕನ್ನಡ (Kannada)", "kn-IN"),
    "hi": ("हिन्दी (Hindi)", "hi-IN"),
    "ta": ("தமிழ் (Tamil)", "ta-IN"),
    "te": ("తెలుగు (Telugu)", "te-IN"),
    "ml": ("മലയാളം (Malayalam)", "ml-IN"),
    "ur": ("اردو (Urdu)", "ur-IN"),
    "bn": ("বাংলা (Bengali)", "bn-IN"),
}
STATUSES = ["Pending", "Processing", "Solved"]
PRIORITIES = ["High", "Medium", "Low"]
SORT_OPTIONS = {
    "priority": "Priority (default)",
    "newest": "Newest first",
    "upvotes": "Most upvoted",
}


def translate_complaint_text(text, source_language):
    """Translate complaint text to English through an optional LibreTranslate endpoint."""
    endpoint = os.environ.get("CITYSOLUTION_TRANSLATE_URL", "").strip()
    if not text or source_language == "en" or not endpoint:
        return None
    payload = {
        "q": text[:2000],
        "source": source_language,
        "target": "en",
        "format": "text",
    }
    api_key = os.environ.get("CITYSOLUTION_TRANSLATE_API_KEY", "").strip()
    if api_key:
        payload["api_key"] = api_key
    request_data = json.dumps(payload).encode("utf-8")
    translate_request = urllib.request.Request(
        endpoint,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(translate_request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
        return None
    translated = str(result.get("translatedText") or "").strip()
    return translated[:2000] or None


def translate_interface_with_google(texts, target_language):
    """Translate UI-only strings in bounded batches using Google Translate."""
    boundary = "ZXQ7F81QXZ"
    batches = []
    batch = []
    batch_length = 0
    for text in texts:
        separator_length = len(boundary) + 2 if batch else 0
        if batch and batch_length + separator_length + len(text) > 1200:
            batches.append(batch)
            batch = []
            batch_length = 0
            separator_length = 0
        batch.append(text)
        batch_length += separator_length + len(text)
    if batch:
        batches.append(batch)

    translations = []
    for batch in batches:
        query = ("\n" + boundary + "\n").join(batch)
        query_string = urllib.parse.urlencode({
            "client": "gtx",
            "sl": "en",
            "tl": target_language,
            "dt": "t",
            "q": query,
        })
        translate_request = urllib.request.Request(
            "https://translate.googleapis.com/translate_a/single?" + query_string,
            headers={"User-Agent": "CitySolution/1.0"},
        )
        with urllib.request.urlopen(translate_request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, list) or not result or not isinstance(result[0], list):
            raise ValueError("The translation service returned an invalid response.")
        translated_batch = "".join(
            segment[0]
            for segment in result[0]
            if isinstance(segment, list) and segment and isinstance(segment[0], str)
        ).split(boundary)
        translated_batch = [text.strip() for text in translated_batch]
        if len(translated_batch) != len(batch) or any(not text for text in translated_batch):
            raise ValueError("The translation service returned an incomplete translation.")
        translations.extend(translated_batch)
    return translations


@app.route("/translate-interface", methods=["POST"])
def translate_interface():
    """Translate static interface strings using a configured or default service."""
    endpoint = os.environ.get("CITYSOLUTION_TRANSLATE_URL", "").strip()

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON translation request is required."), 400
    texts = payload.get("texts")
    target_language = payload.get("language")
    if (
        not isinstance(texts, list)
        or not texts
        or len(texts) > 120
        or any(not isinstance(text, str) or not text.strip() or len(text) > 300 for text in texts)
        or target_language not in COMPLAINT_LANGUAGES
        or target_language == "en"
    ):
        return jsonify(error="The language or interface text batch is invalid."), 400
    if session.get("complaint_interface_language") != target_language:
        return jsonify(error="Choose this language on the complaint form first."), 403

    if not endpoint:
        try:
            translations = translate_interface_with_google(texts, target_language)
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
            app.logger.exception("Default interface translation request failed")
            return jsonify(error="The translation service could not translate this page."), 502
        return jsonify(translations=translations)

    translate_payload = {
        "q": texts,
        "source": "en",
        "target": target_language,
        "format": "text",
    }
    api_key = os.environ.get("CITYSOLUTION_TRANSLATE_API_KEY", "").strip()
    if api_key:
        translate_payload["api_key"] = api_key
    translate_request = urllib.request.Request(
        endpoint,
        data=json.dumps(translate_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(translate_request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
        app.logger.exception("Configured interface translation service request failed")
        return jsonify(error="The translation service could not translate this page."), 502

    if isinstance(result, list):
        translations = [
            item.get("translatedText") if isinstance(item, dict) else None
            for item in result
        ]
    elif isinstance(result, dict) and isinstance(result.get("translatedText"), list):
        translations = result["translatedText"]
    elif isinstance(result, dict) and len(texts) == 1:
        translations = [result.get("translatedText")]
    else:
        translations = None
    if (
        not isinstance(translations, list)
        or len(translations) != len(texts)
        or any(not isinstance(text, str) or not text.strip() for text in translations)
    ):
        app.logger.error("Configured interface translation service returned an invalid batch")
        return jsonify(error="The translation service returned an incomplete translation."), 502
    return jsonify(translations=translations)


@app.route("/complaint-language", methods=["POST"])
def set_complaint_interface_language():
    payload = request.get_json(silent=True)
    language = payload.get("language") if isinstance(payload, dict) else None
    if language not in COMPLAINT_LANGUAGES:
        return jsonify(error="Choose a supported complaint language."), 400
    session["complaint_interface_language"] = language
    return jsonify(language=language)


def authority_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("authority_authenticated"):
            return redirect(url_for("authority_login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped_view


def current_citizen_user():
    user_id = session.get("citizen_user_id")
    if not user_id:
        return None
    user = db.get_citizen_user(user_id)
    if user is None:
        session.pop("citizen_user_id", None)
    return user


def current_voter_id():
    user = current_citizen_user()
    if user:
        return f"citizen:{user['id']}"
    voter_id = session.get("voter_id")
    if not voter_id:
        voter_id = uuid.uuid4().hex
        session["voter_id"] = voter_id
    return voter_id


def citizen_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_citizen_user():
            return redirect(url_for("citizen_login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped_view

CATEGORY_ICONS = {
    "Road Maintenance": "\U0001F6E3\uFE0F",       # motorway
    "Storm Water Drain": "\U0001F327\uFE0F",       # cloud with rain
    "Solid Waste": "\U0001F5D1\uFE0F",             # wastebasket
    "Street Light / Electrical": "\U0001F4A1",     # light bulb
    "Water Supply": "\U0001F6B0",                  # potable water
    "Sewage / Sanitation": "\U0001F6BD",           # toilet
    "Stray Animals": "\U0001F415",                 # dog
    "Parks & Trees": "\U0001F333",                 # tree
    "Encroachment": "\U0001F3D7\uFE0F",            # building construction
    "Others": "\U0001F4CB",                        # clipboard
}


def category_photo_path(category):
    slug = re.sub(r"[^a-z0-9]+", "-", (category or "").lower()).strip("-")
    filename = f"{slug}.jpg"
    path = os.path.join(BASE_DIR, "static", "category_photos", filename)
    if not os.path.isfile(path):
        filename = "others.jpg"
    return f"category_photos/{filename}"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def valid_profile_image(upload):
    extension = upload.filename.rsplit(".", 1)[1].lower()
    expected_format = {
        "png": "PNG",
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "webp": "WEBP",
    }[extension]
    try:
        image = Image.open(upload.stream)
        image_format = image.format
        image.verify()
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
        return False
    finally:
        upload.stream.seek(0)
    return image_format == expected_format


def normalize_phone_number(value):
    phone = re.sub(r"[\s().-]", "", value or "")
    if re.fullmatch(r"[6-9]\d{9}", phone):
        return f"+91{phone}"
    if phone.startswith("+") and re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        return phone
    raise ValueError("Enter a valid mobile number, including country code if outside India.")


def parse_coordinates(latitude_value, longitude_value):
    latitude_missing = latitude_value is None or str(latitude_value).strip() == ""
    longitude_missing = longitude_value is None or str(longitude_value).strip() == ""
    if latitude_missing and longitude_missing:
        return None, None
    if latitude_missing or longitude_missing:
        raise ValueError("Both GPS coordinates are required.")
    try:
        latitude = float(latitude_value)
        longitude = float(longitude_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("GPS coordinates must be numeric.") from exc
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("GPS latitude is out of range.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("GPS longitude is out of range.")
    return latitude, longitude


@app.context_processor
def inject_helpers():
    """Makes effective_priority() and category icons callable from every
    template, so the priority actually shown/sorted (raw priority + upvote
    escalation, unless locked) and category iconography stay consistent
    across the home page, complaints list, complaint detail, and
    dashboard - not just wherever it was explicitly passed in."""
    citizen_user = current_citizen_user()
    return {
        "effective_priority": effective_priority,
        "category_icons": CATEGORY_ICONS,
        "category_photo_path": category_photo_path,
        "citizen_user": citizen_user,
    }


# Also registered as true Jinja *globals* (not just per-request context) so
# that _macros.html's dash_card()/complaint_row() macros can see them even
# when imported with the default (context-free) {% from ... import %) -
# this is what lets a single macro definition serve both full page renders
# and the live-update partial routes below.
app.jinja_env.globals.update(
    effective_priority=effective_priority,
    category_icons=CATEGORY_ICONS,
    category_photo_path=category_photo_path,
    PRIORITIES=PRIORITIES,
    STATUSES=STATUSES,
    ALL_CATEGORIES=ALL_CATEGORIES,
)


def live_stats():
    """db.get_stats() plus derived scalar counts that the overview cards display."""
    stats = db.get_stats()
    high_count = next((p["cnt"] for p in stats["by_priority"] if p["priority"] == "High"), 0)
    pending_count = next((s["cnt"] for s in stats["by_status"] if s["status"] == "Pending"), 0)
    solved_count = next((s["cnt"] for s in stats["by_status"] if s["status"] == "Solved"), 0)
    processing_count = next((s["cnt"] for s in stats["by_status"] if s["status"] == "Processing"), 0)
    fake_count = stats.get("fake", 0)
    stats.update(
        high_count=high_count,
        pending_count=pending_count,
        solved_count=solved_count,
        processing_count=processing_count,
        fake_count=fake_count,
    )
    return stats


@app.route("/authority-login", methods=["GET", "POST"])
def authority_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if hmac.compare_digest(username, AUTHORITY_USERNAME) and hmac.compare_digest(password, AUTHORITY_PASSWORD):
            session.clear()
            session["authority_authenticated"] = True
            next_url = request.form.get("next") or url_for("dashboard")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("dashboard")
            return redirect(next_url)
        flash("Invalid authority credentials.", "error")
    return render_template("authority_login.html", next_url=request.args.get("next", ""))


@app.route("/authority-logout")
def authority_logout():
    session.pop("authority_authenticated", None)
    return redirect(url_for("home"))


@app.route("/citizen-signup", methods=["GET", "POST"])
def citizen_signup():
    if current_citizen_user():
        return redirect(url_for("citizen_account"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        if not name or len(name) > 80:
            flash("Enter your name (up to 80 characters).", "error")
        elif not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
            flash("Username must be 3-32 characters using letters, numbers, dots, dashes, or underscores.", "error")
        elif len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 10 or len(password) > 128:
            flash("Choose a password between 10 and 128 characters.", "error")
        elif password != password_confirm:
            flash("The passwords do not match.", "error")
        else:
            try:
                user_id = db.create_citizen_user(
                    username, name, email, generate_password_hash(password)
                )
            except db.IntegrityError:
                flash("That username or email already has an account. Try signing in.", "error")
            else:
                session.clear()
                session["citizen_user_id"] = user_id
                flash("Your citizen account is ready.", "success")
                return redirect(url_for("citizen_account"))
    return render_template("citizen_signup.html")


@app.route("/citizen-login", methods=["GET", "POST"])
def citizen_login():
    if current_citizen_user():
        return redirect(url_for("citizen_account"))
    next_url = request.args.get("next", "")
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = db.get_citizen_user_by_login(identifier) if identifier else None
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["citizen_user_id"] = user["id"]
            flash("Welcome back.", "success")
            requested_next = request.form.get("next", "")
            if requested_next.startswith("/") and not requested_next.startswith("//"):
                return redirect(requested_next)
            return redirect(url_for("citizen_account"))
        flash("We could not sign you in with those details.", "error")
    return render_template("citizen_login.html", next_url=next_url)


@app.route("/citizen-logout", methods=["POST"])
def citizen_logout():
    session.pop("citizen_user_id", None)
    flash("You have signed out.", "success")
    return redirect(url_for("home"))


@app.route("/account", methods=["GET", "POST"])
@citizen_required
def citizen_account():
    user = current_citizen_user()
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "profile":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            city = request.form.get("city", "").strip()
            area = request.form.get("area", "").strip()
            ward = request.form.get("ward", "").strip()
            if not name or len(name) > 80:
                flash("Enter your name (up to 80 characters).", "error")
            elif len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                flash("Enter a valid email address.", "error")
            elif len(city) > 100 or len(area) > 100 or len(ward) > 100:
                flash("City, area, and ward must each be 100 characters or fewer.", "error")
            else:
                try:
                    db.update_citizen_profile(
                        user["id"],
                        name,
                        email,
                        city,
                        area,
                        ward,
                        "",
                    )
                except db.IntegrityError:
                    flash("That email address is already linked to another account.", "error")
                else:
                    flash("Your profile and area details have been updated.", "success")
                    return redirect(url_for("citizen_account"))
        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            password_confirm = request.form.get("password_confirm", "")
            account_record = db.get_citizen_user_by_login(user["email"])
            if not account_record or not check_password_hash(
                account_record["password_hash"], current_password
            ):
                flash("Your current password is incorrect.", "error")
            elif len(new_password) < 10 or len(new_password) > 128:
                flash("Choose a password between 10 and 128 characters.", "error")
            elif new_password != password_confirm:
                flash("The new passwords do not match.", "error")
            else:
                db.update_citizen_password(
                    user["id"], generate_password_hash(new_password)
                )
                flash("Your password has been changed.", "success")
                return redirect(url_for("citizen_account"))
        else:
            flash("That profile action is not available.", "error")
            return redirect(url_for("citizen_account"))

    complaints = db.get_citizen_complaints(user["id"])
    complaint_summary = {
        "total": len(complaints),
        "pending": sum(complaint["status"] == "Pending" for complaint in complaints),
        "in_progress": sum(complaint["status"] == "Processing" for complaint in complaints),
        "resolved": sum(complaint["status"] == "Solved" for complaint in complaints),
    }
    return render_template(
        "citizen_account.html",
        user=user,
        cities=CITIES,
        complaint_languages=COMPLAINT_LANGUAGES,
        complaint_summary=complaint_summary,
    )


@app.route("/my-reports")
@citizen_required
def citizen_reports():
    user = current_citizen_user()
    return render_template(
        "citizen_reports.html",
        user=user,
        complaints=db.get_citizen_complaints(user["id"]),
    )


@app.route("/")
def home():
    stats = live_stats()
    user = current_citizen_user()
    my_reports = db.get_citizen_complaints(user["id"]) if user else []
    status_counts = {status: 0 for status in STATUSES}
    source_rows = my_reports if user else stats["by_status"]
    for row in source_rows:
        if user:
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        else:
            status_counts[row["status"]] = row["cnt"]
    return render_template(
        "index.html",
        stats=stats,
        status_counts=status_counts,
        report_total=len(my_reports) if user else stats["total"],
        is_personal_dashboard=bool(user),
    )


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        account_user = current_citizen_user()
        citizen_name = account_user["name"] if account_user else request.form.get("citizen_name", "").strip()
        citizen_email = account_user["email"] if account_user else request.form.get("citizen_email", "").strip()
        email_opt_in = (
            bool(account_user["email_notifications"])
            if account_user
            else request.form.get("email_consent") == "on"
        )
        if email_opt_in and not citizen_email:
            flash("Enter an email address to receive email updates.", "error")
            return redirect(url_for("submit"))
        if not account_user and not email_opt_in:
            flash("Choose email updates so you can receive complaint progress notifications.", "error")
            return redirect(url_for("submit"))
        city = request.form.get("city", "").strip()
        location = request.form.get("location", "").strip()
        if account_user:
            city = city or (
                account_user["area"]
                if account_user["area"] in CITIES
                else account_user["city"] if account_user["city"] in CITIES else ""
            )
            if not location:
                location = ", ".join(
                    value for value in (account_user["city"], account_user["ward"]) if value
                )
        description = request.form.get("description", "").strip()
        source_language = request.form.get(
            "source_language",
            "en",
        ).strip()
        if source_language not in COMPLAINT_LANGUAGES:
            source_language = "en"
        translated_description = translate_complaint_text(description, source_language)
        processing_description = translated_description or description
        category = request.form.get("category", "").strip()
        image_file = request.files.get("image")
        try:
            latitude, longitude = parse_coordinates(
                request.form.get("latitude", "").strip(),
                request.form.get("longitude", "").strip(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("submit"))

        image_path = None
        has_image = image_file and image_file.filename and allowed_file(image_file.filename)

        if not description and not has_image:
            flash("Please provide a description or upload a photo of the problem.", "error")
            return redirect(url_for("submit"))
        if category not in ALL_CATEGORIES:
            flash("Please choose a valid complaint class.", "error")
            return redirect(url_for("submit"))

        matches = db.find_similar_complaints(
            processing_description, city=city, latitude=latitude, longitude=longitude,
            category=category, location=location,
            include_demo=app.config["CITYSOLUTION_PRESENTATION_MODE"],
            image_bytes=image_file.read() if has_image else None,
        )
        if has_image:
            image_file.seek(0)
        if matches:
            match = matches[0]
            flash(
                f"A similar issue has already been reported as complaint "
                f"#{match['id']:04d}. No new complaint was filed. Review it "
                "and choose “Report Existing Complaint” if you want to support it.",
                "error",
            )
            return redirect(url_for(
                "complaint_detail",
                complaint_id=match["id"],
                duplicate="1",
            ))

        if has_image:
            ext = image_file.filename.rsplit(".", 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            full_path = os.path.join(UPLOAD_DIR, fname)
            image_file.save(full_path)
            image_path = f"uploads/{fname}"
            complaint_type = "image"
        else:
            complaint_type = "text"

        priority = score_priority(category, processing_description)

        new_id = db.add_complaint(
            complaint_type=complaint_type,
            description=description,
            image_path=image_path,
            city=city,
            location=location,
            category=category,
            confidence=None,
            priority=priority,
            citizen_name=citizen_name,
            citizen_email=citizen_email,
            latitude=latitude,
            longitude=longitude,
            email_opt_in=email_opt_in,
            translated_description=translated_description,
            source_language=source_language,
            citizen_user_id=account_user["id"] if account_user else None,
        )
        flash(
            f"Complaint #{new_id} submitted under '{category}', priority: {priority}.",
            "success",
        )
        if email_opt_in:
            if not email_is_configured():
                flash("Email notifications are not configured yet; set the SMTP settings to receive email.", "error")
            elif not send_email(
                citizen_email,
                f"Complaint #{new_id:04d} received",
                f"Your {category} complaint has been filed. Current status: Pending.",
            ):
                flash("Your complaint was filed, but the confirmation email could not be sent.", "error")
        events.broadcast(
            "new_complaint", id=new_id, category=category, city=city,
            message=f"New {category} complaint" + (f" in {city}" if city else " filed"),
            stats=live_stats(),
        )
        return redirect(url_for("track_complaint", complaint_id=new_id))

    return render_template(
        "submit.html", cities=CITIES, categories=ALL_CATEGORIES,
        complaint_languages=COMPLAINT_LANGUAGES,
        translation_configured=bool(os.environ.get("CITYSOLUTION_TRANSLATE_URL", "").strip()),
        citizen_user=current_citizen_user(),
    )


@app.route("/api/duplicates", methods=["POST"])
def api_duplicates():
    if request.mimetype == "multipart/form-data":
        payload = request.form
        image_upload = request.files.get("image")
        image_bytes = image_upload.read() if image_upload and image_upload.filename else None
    else:
        payload = request.get_json(silent=True) or {}
        image_bytes = None
    description = str(payload.get("description") or "").strip()[:2000]
    city = str(payload.get("city") or "").strip() or None
    location = str(payload.get("location") or "").strip() or None
    category = str(payload.get("category") or "").strip() or None
    try:
        latitude, longitude = parse_coordinates(payload.get("latitude"), payload.get("longitude"))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    matches = db.find_similar_complaints(
        description, city=city, latitude=latitude, longitude=longitude,
        category=category, location=location,
        include_demo=app.config["CITYSOLUTION_PRESENTATION_MODE"],
        image_bytes=image_bytes,
    )
    if matches:
        voter_id = current_voter_id()
        for match in matches:
            match["has_upvoted"] = db.has_upvoted_complaint(match["id"], voter_id)
    return jsonify(matches=matches)


@app.route("/complaints")
@authority_required
def my_complaints():
    complaints = db.get_all_complaints()
    return render_template("my_complaints.html", complaints=complaints, cities=CITIES)


@app.route("/track", methods=["GET", "POST"])
def track_complaint():
    tracked = None
    complaint_id = request.args.get("complaint_id", "")
    contact = ""
    error = None

    user = current_citizen_user()
    if request.method == "GET" and complaint_id.isdigit() and user:
        owner_complaint = db.get_complaint(int(complaint_id))
        if owner_complaint and owner_complaint["citizen_user_id"] == user["id"]:
            contact = user["email"]

    if request.method == "POST":
        complaint_id = request.form.get("complaint_id", "").strip()
        contact = request.form.get("contact", "").strip()
        complaint = None
        if complaint_id.isdigit() and len(complaint_id) <= 10 and len(contact) <= 254:
            complaint = db.get_complaint(int(complaint_id))

        email = (complaint["citizen_email"] or "").strip() if complaint else ""
        phone = (complaint["citizen_phone"] or "").strip() if complaint else ""
        email_matches = bool(email) and hmac.compare_digest(
            contact.casefold().encode("utf-8"), email.casefold().encode("utf-8")
        )
        try:
            normalized_contact_phone = normalize_phone_number(contact)
        except ValueError:
            normalized_contact_phone = ""
        phone_matches = bool(phone) and hmac.compare_digest(
            normalized_contact_phone.encode("utf-8"), phone.encode("utf-8")
        )

        if complaint and (email_matches or phone_matches):
            category_photo = re.sub(r"[^a-z0-9]+", "-", complaint["category"].lower()).strip("-")
            tracked = {
                "id": complaint["id"],
                "category": complaint["category"],
                "status": complaint["status"],
                "created_at": complaint["created_at"],
                "image_path": complaint["image_path"] or f"category_photos/{category_photo}.jpg",
                "representative_image": not complaint["image_path"] or complaint["image_path"].startswith("category_photos/"),
            }
        else:
            error = "We could not verify those details. Check the complaint number and contact used when filing."

    return render_template(
        "track_complaint.html",
        tracked=tracked,
        complaint_id=complaint_id,
        contact=contact,
        error=error,
        statuses=STATUSES,
    )


@app.route("/complaint/<int:complaint_id>")
def complaint_detail(complaint_id):
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("home"))
    voter_id = current_voter_id()
    return render_template(
        "complaint_detail.html",
        c=complaint,
        has_upvoted=db.has_upvoted_complaint(complaint_id, voter_id),
    )


@app.route("/service-worker.js")
def service_worker():
    response = send_file(
        os.path.join(BASE_DIR, "static", "service-worker.js"),
        mimetype="application/javascript",
    )
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/dashboard")
@authority_required
def dashboard():
    # Authority desk always queries the full complaint table (get_all_complaints
    # has no default limit) - filters below only narrow what's shown on request,
    # they never restrict which complaints authorities are able to see.
    city = request.args.get("city") or None
    category = request.args.get("category") or None
    complaint_type = request.args.get("intake_type") or None
    status = request.args.get("status") or None
    priority = request.args.get("priority") or None
    sort_by = request.args.get("sort") or "priority"
    if sort_by not in SORT_OPTIONS:
        sort_by = "priority"
    complaints = db.get_all_complaints(
        city=city, category=category, status=status, priority=priority,
        complaint_type=complaint_type, sort_by=sort_by,
    )
    stats = live_stats()
    return render_template(
        "dashboard.html",
        complaints=complaints,
        stats=stats,
        clear_complaints_csrf_token=session.setdefault(
            "clear_complaints_csrf_token", uuid.uuid4().hex
        ),
        cities=CITIES,
        categories=ALL_CATEGORIES,
        statuses=STATUSES,
        priorities=PRIORITIES,
        sort_options=SORT_OPTIONS,
        filters={"city": city, "category": category, "intake_type": complaint_type, "status": status, "priority": priority, "sort": sort_by},
    )


@app.route("/authority/demo-complaints", methods=["POST"])
@authority_required
def add_demo_complaints():
    from generate_sample_complaints_excel import build_sample_rows

    rows = build_sample_rows(n=150)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.import_demo_complaints([
        {
            "demo_key": f"citysolution-demo-{index:03d}",
            "description": ". " + row["description"],
            "city": row["area"],
            "location": f"Demo location in {row['area']}",
            "category": row["category"],
            "confidence": row["confidence"],
            "priority": row["priority"],
            "created_at": created_at,
        }
        for index, row in enumerate(rows, start=1)
    ])
    count = db.count_demo_complaints()
    flash(f"Demo data set ready: {count} clearly labeled demo complaints.", "success")
    return redirect(url_for("dashboard"))


@app.route("/authority/clear-complaints", methods=["POST"])
@authority_required
def clear_all_complaints():
    expected_token = session.get("clear_complaints_csrf_token", "")
    submitted_token = request.form.get("csrf_token", "")
    if not expected_token or not hmac.compare_digest(submitted_token, expected_token):
        return "Invalid complaint deletion form token.", 400
    if request.form.get("confirm") != "yes":
        flash("Confirm that you want to permanently delete every complaint.", "error")
        return redirect(url_for("dashboard"))

    session.pop("clear_complaints_csrf_token", None)
    deleted_complaints = db.clear_all_complaints()
    for complaint_id, image_path in deleted_complaints:
        events.broadcast("delete", id=complaint_id)
        if image_path and image_path.startswith("uploads/"):
            filename = os.path.basename(image_path)
            if filename and filename == image_path[len("uploads/"):]:
                try:
                    os.remove(os.path.join(UPLOAD_DIR, filename))
                except FileNotFoundError:
                    pass
                except OSError:
                    app.logger.exception(
                        "Could not remove image for deleted complaint %s",
                        complaint_id,
                    )

    events.broadcast("migration", stats=live_stats())
    flash(
        f"Deleted {len(deleted_complaints)} complaints. "
        "The next complaint number will be #1.",
        "success",
    )
    return redirect(url_for("dashboard"))


@app.route("/complaint/<int:complaint_id>/update", methods=["POST"])
@authority_required
def update_complaint(complaint_id):
    complaint = db.get_complaint(complaint_id)
    status = request.form.get("status")
    category = request.form.get("category")
    priority = request.form.get("priority")
    is_fake = request.form.get("is_fake") == "on"
    priority_locked = request.form.get("priority_locked") == "on"
    db.update_complaint(
        complaint_id, status=status, category=category, priority=priority,
        is_fake=is_fake, priority_locked=priority_locked,
    )
    flash(f"Complaint #{complaint_id} updated.", "success")
    if complaint and status and status != complaint["status"]:
        email_updates_enabled = True
        if complaint["citizen_user_id"]:
            citizen_owner = db.get_citizen_user(complaint["citizen_user_id"])
            if citizen_owner:
                email_updates_enabled = bool(citizen_owner["email_notifications"])
        if (
            complaint["email_opt_in"]
            and complaint["citizen_email"]
            and email_updates_enabled
        ):
            if email_is_configured():
                if status == "Solved":
                    resolved_complaint = db.get_complaint(complaint_id)
                    ok, result = send_resolution_email_for_complaint(resolved_complaint)
                    if ok:
                        flash("Resolution email sent to the citizen.", "success")
                    else:
                        flash(f"Status updated, but the resolution email could not be sent: {result}", "error")
                elif not send_email(
                    complaint["citizen_email"],
                    f"Complaint #{complaint_id:04d} status update",
                    f"Your complaint status changed from {complaint['status']} to {status}.",
                ):
                    flash("Status updated, but the email notification could not be sent.", "error")
            else:
                flash("Status updated, but email notifications are not configured.", "error")
        if complaint["sms_opt_in"] and complaint["citizen_phone"]:
            if sms_is_configured():
                if not send_sms(
                    complaint["citizen_phone"],
                    f"CitySolution: complaint #{complaint_id:04d} is now {status}.",
                ):
                    flash("Status updated, but the SMS notification could not be sent.", "error")
            else:
                flash("Status updated, but SMS notifications are not configured.", "error")
    events.broadcast(
        "update", id=complaint_id, status=status,
        message=f"Complaint #{complaint_id:04d} updated" + (f": {status}" if status else ""),
        stats=live_stats(),
    )
    return redirect(url_for("dashboard"))


def build_resolution_email_body(complaint):
    complaint_id = complaint["id"]
    user_name = complaint["citizen_name"] or "Citizen"
    complaint_category = complaint["category"] or "Complaint"
    complaint_description = complaint["description"] or "Not provided"
    complaint_location = complaint["location"] or "Not provided"
    return (
        f"Dear {user_name},\n\n"
        f"Your complaint #{complaint_id} regarding {complaint_category} has been successfully resolved by the concerned authority.\n"
        f"Complaint: {complaint_description}\n"
        f"Location: {complaint_location}\n"
        "Status: Solved\n\n"
        "Thank you for reporting this issue and helping us improve our city.\n\n"
        "Regards,\n"
        "Smart City Complaint Management System"
    )


def send_resolution_email_for_complaint(complaint, allow_resend=False):
    if complaint["status"] != "Solved":
        return False, "Email can only be sent after the complaint is marked as Solved."
    if complaint["email_sent"] and not allow_resend:
        return False, "A resolution email has already been sent to the complaint submitter."
    if not complaint["email_opt_in"]:
        return False, "The citizen did not opt in to email notifications."
    if not complaint["citizen_email"]:
        return False, "This complaint does not have a citizen email address saved."
    if complaint["citizen_user_id"]:
        citizen_owner = db.get_citizen_user(complaint["citizen_user_id"])
        if citizen_owner and not citizen_owner["email_notifications"]:
            return False, "Email notifications are disabled in the citizen's account."
    if not email_is_configured():
        return False, "Failed to send email. Please check the email service configuration."

    body = build_resolution_email_body(complaint)
    subject = f"Your Smart City Complaint #{complaint['id']} Has Been Resolved"
    if not send_email(complaint["citizen_email"], subject, body):
        return False, "Failed to send email. Please check the email service configuration."

    db.update_complaint(
        complaint["id"],
        email_sent=True,
        email_sent_at=datetime.now().astimezone().strftime("%d %b %Y, %I:%M %p"),
    )
    return True, db.get_complaint(complaint["id"])["email_sent_at"]


@app.route("/api/complaints/<int:complaint_id>/send-email", methods=["POST"])
@authority_required
def api_send_complaint_email(complaint_id):
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        return jsonify({"ok": False, "error": "Complaint not found."}), 404

    payload = request.get_json(silent=True) or {}
    allow_resend = payload.get("resend") is True
    ok, result = send_resolution_email_for_complaint(complaint, allow_resend=allow_resend)
    if not ok:
        status_code = 409 if complaint["email_sent"] and not allow_resend else 400
        return jsonify({
            "ok": False,
            "error": result,
            "requires_confirmation": status_code == 409,
        }), status_code

    return jsonify({
        "ok": True,
        "message": "✓ Email sent successfully to the complaint submitter.",
        "email_sent_at": result,
    })


@app.route("/complaint/<int:complaint_id>/email-completion", methods=["POST"])
@authority_required
def email_completion(complaint_id):
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("my_complaints"))

    ok, result = send_resolution_email_for_complaint(complaint)
    if ok:
        flash(f"✓ Email sent successfully to the complaint submitter.", "success")
    else:
        flash(result, "error")
    return redirect(url_for("complaint_detail", complaint_id=complaint_id))


@app.route("/complaint/<int:complaint_id>/delete", methods=["POST"])
@authority_required
def delete_complaint(complaint_id):
    """Only Solved complaints can be deleted - enforced here too, not just
    hidden in the UI, so this can't be done by directly POSTing to the
    route on a complaint that's still open."""
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("dashboard"))

    if complaint["status"] != "Solved":
        flash(f"Complaint #{complaint_id} can only be deleted once it's marked Solved.", "error")
        return redirect(request.form.get("next") or url_for("dashboard"))

    if complaint["image_path"] and complaint["image_path"].startswith("uploads/"):
        photo_path = os.path.join(
            UPLOAD_DIR, complaint["image_path"].split("/", 1)[1]
        )
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.delete_complaint(complaint_id)
    flash(f"Complaint #{complaint_id} deleted.", "success")
    events.broadcast("delete", id=complaint_id, stats=live_stats())
    return redirect(request.form.get("next") or url_for("dashboard"))


@app.route("/complaint/<int:complaint_id>/upvote", methods=["POST"])
def upvote_complaint(complaint_id):
    """Allow one upvote per citizen account or guest browser session."""
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("home"))
    if complaint["is_demo"] and not app.config["CITYSOLUTION_PRESENTATION_MODE"]:
        flash("Project sample complaints cannot be upvoted outside presentation mode.", "error")
        return redirect(url_for("complaint_detail", complaint_id=complaint_id))

    voter_id = current_voter_id()
    if db.upvote_complaint(complaint_id, voter_id):
        flash(f"You upvoted complaint #{complaint_id:04d}.", "success")
        events.broadcast("upvote", id=complaint_id, stats=live_stats())
    else:
        flash(f"You've already upvoted complaint #{complaint_id:04d}.", "error")

    next_url = request.form.get("next") or url_for("complaint_detail", complaint_id=complaint_id)
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("complaint_detail", complaint_id=complaint_id)
    return redirect(next_url)


@app.route("/api/stats")
@authority_required
def api_stats():
    return jsonify(db.get_stats())


@app.route("/stream")
@authority_required
def stream():
    """Server-Sent Events endpoint - one long-lived connection per open
    browser tab. Every change elsewhere in the app (see events.broadcast()
    calls in submit/update_complaint/delete_complaint/upvote_complaint)
    gets pushed down every open connection as a small JSON message; static/
    live.js is what's listening on the browser side.

    Requires the dev server to run with threaded=True (see bottom of this
    file) - otherwise this one held-open connection would block every
    other request in the single-threaded Werkzeug dev server."""
    def event_stream():
        q = events.subscribe()
        try:
            yield "retry: 3000\n\n"  # tell the browser how fast to retry if the connection drops
            while True:
                try:
                    message = q.get(timeout=15)
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"  # SSE comment line - keeps the connection alive through proxies
        except GeneratorExit:
            pass
        finally:
            events.unsubscribe(q)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/partials/dash-card/<int:complaint_id>")
@authority_required
def partial_dash_card(complaint_id):
    """Returns just the freshly-rendered HTML for one dashboard card -
    fetched by the dashboard's live.js handler after an SSE event says
    this complaint changed, so the card it swaps in is guaranteed to be
    identical to what a full page reload would show (same macro, same
    data). 404 (empty body) if the complaint was deleted in the meantime -
    the caller treats that as "remove this card"."""
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        return "", 404
    next_url = request.args.get("next") or url_for("dashboard")
    return render_template("_dash_card_solo.html", c=complaint, next_url=next_url)


@app.route("/partials/complaint-row/<int:complaint_id>")
@authority_required
def partial_complaint_row(complaint_id):
    """Same idea as partial_dash_card, for the row used on the complaints
    list and the home page's Recently Filed section."""
    complaint = db.get_complaint(complaint_id)
    if not complaint:
        return "", 404
    return render_template("_complaint_row_solo.html", c=complaint)


@app.route("/admin/migrate-complaints", methods=["GET", "POST"])
@authority_required
def migrate_laptop_complaints():
    if not app.config["CITYSOLUTION_ENABLE_MIGRATION"]:
        return "", 404

    csrf_token = session.setdefault("migration_csrf_token", uuid.uuid4().hex)
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        if not hmac.compare_digest(submitted_token, csrf_token):
            return "Invalid migration form token.", 400

        workbook = request.files.get("workbook")
        if not workbook or not workbook.filename:
            flash("Choose the redacted laptop migration workbook.", "error")
            return redirect(url_for("migrate_laptop_complaints"))
        if not workbook.filename.lower().endswith(".xlsx"):
            flash("Upload an .xlsx migration workbook.", "error")
            return redirect(url_for("migrate_laptop_complaints"))

        try:
            imported, skipped = migrate_complaints.import_redacted_workbook(workbook.stream)
        except (OSError, ValueError) as exc:
            app.logger.warning("Complaint migration workbook rejected: %s", exc)
            flash(f"Migration was not completed: {exc}", "error")
            return redirect(url_for("migrate_laptop_complaints"))

        events.broadcast(
            "migration",
            imported=imported,
            skipped=skipped,
            stats=live_stats(),
        )
        flash(
            f"Migration complete: {imported} imported; {skipped} already-migrated records skipped.",
            "success",
        )
        return redirect(url_for("migrate_laptop_complaints"))

    return render_template("migrate_complaints.html", csrf_token=csrf_token)


@app.route("/admin/import-sample-complaints", methods=["GET", "POST"])
@authority_required
def import_sample_complaints():
    if not app.config["CITYSOLUTION_ENABLE_SAMPLE_IMPORT"]:
        return "", 404
    if not app.config["CITYSOLUTION_PUBLIC_SAMPLE_DATA"]:
        return "Enable the public sample-data notice before importing sample complaints.", 503

    csrf_token = session.setdefault("sample_import_csrf_token", uuid.uuid4().hex)
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        if not hmac.compare_digest(submitted_token, csrf_token):
            return "Invalid sample import form token.", 400

        workbook = request.files.get("workbook")
        if not workbook or not workbook.filename:
            flash("Choose the complaint workbook to import.", "error")
            return redirect(url_for("import_sample_complaints"))
        if not workbook.filename.lower().endswith(".xlsx"):
            flash("Upload an .xlsx workbook.", "error")
            return redirect(url_for("import_sample_complaints"))

        try:
            import create_presentation_database

            records = create_presentation_database.read_complaints(workbook.stream)
            deleted, imported = db.replace_generated_demo_complaints(records)
        except (OSError, ValueError) as exc:
            app.logger.warning("Sample complaint workbook rejected: %s", exc)
            flash(f"Sample import was not completed: {exc}", "error")
            return redirect(url_for("import_sample_complaints"))

        skipped = len(records) - imported
        events.broadcast(
            "migration",
            imported=imported,
            skipped=skipped,
            deleted=deleted,
            stats=live_stats(),
        )
        flash(
            f"Sample import complete: {deleted} old generated demo records removed; "
            f"{imported} workbook samples added; {skipped} already-imported rows skipped.",
            "success",
        )
        return redirect(url_for("import_sample_complaints"))

    return render_template(
        "import_sample_complaints.html",
        csrf_token=csrf_token,
    )


if __name__ == "__main__":
    db.init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # threaded=True is required: the /stream route holds a connection open
    # per browser tab, and the single-threaded default dev server would
# otherwise stall every other request behind it.
    app.run(
        host="127.0.0.1" if PRESENTATION_MODE else "0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
    )

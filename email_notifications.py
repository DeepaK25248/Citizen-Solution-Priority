"""Send complaint progress messages through an SMTP server."""

import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


def _smtp_settings():
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if host.casefold() == "smtp.gmail.com":
        password = "".join(password.split())
    sender = os.environ.get("SMTP_FROM", username).strip()
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        return None
    if not all((host, username, password, sender)) or not 1 <= port <= 65535:
        return None
    return host, port, username, password, sender


def _brevo_settings():
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    sender = os.environ.get("BREVO_SENDER_EMAIL", "").strip()
    sender_name = os.environ.get("BREVO_SENDER_NAME", "CitySolution").strip()
    if not api_key or not sender:
        return None
    return api_key, sender, sender_name or "CitySolution"


def email_is_configured():
    return _brevo_settings() is not None or _smtp_settings() is not None


def _send_with_brevo(to_address, subject, body, settings):
    api_key, sender, sender_name = settings
    payload = json.dumps({
        "sender": {"name": sender_name, "email": sender},
        "to": [{"email": to_address}],
        "subject": subject,
        "textContent": body,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                logger.error("Brevo rejected complaint progress email with HTTP %s", response.status)
                return False
        return True
    except (OSError, urllib.error.URLError, ValueError):
        logger.exception("Could not send complaint progress email through Brevo")
        return False


def send_email(to_address, subject, body):
    brevo_settings = _brevo_settings()
    if brevo_settings:
        return _send_with_brevo(to_address, subject, body, brevo_settings)

    settings = _smtp_settings()
    if not settings:
        return False
    host, port, username, password, sender = settings

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException, ValueError):
        logger.exception("Could not send complaint progress email")
        return False

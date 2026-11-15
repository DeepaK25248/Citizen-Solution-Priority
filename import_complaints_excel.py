import os
import sys
from datetime import date, datetime

from openpyxl import load_workbook

import database as db


DEFAULT_WORKBOOK = r"C:\Users\Rashmi\Downloads\citysolution_complaints.xlsx"
REQUIRED_HEADERS = {
    "Priority",
    "Upvotes",
    "Category",
    "Status",
    "Type",
    "Description",
    "Area / Ward",
    "Location / Landmark",
    "Confidence (%)",
    "Fake?",
    "Citizen Name",
    "Citizen Email",
    "Filed On",
}


def text_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def bool_value(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"yes", "true", "1"}


def created_at_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d 00:00")
    result = text_value(value)
    if not result:
        raise ValueError("Filed On is required")
    return result


def parse_row(row, row_number):
    complaint_type = text_value(row.get("Type"))
    if not complaint_type:
        raise ValueError(f"Row {row_number}: Type is required")
    complaint_type = "image" if complaint_type.lower() in {"photo", "image"} else "text"

    category = text_value(row.get("Category"))
    priority = text_value(row.get("Priority"))
    status = text_value(row.get("Status"))
    if not category or not priority or not status:
        raise ValueError(f"Row {row_number}: Category, Priority, and Status are required")

    try:
        confidence = float(row["Confidence (%)"]) if row.get("Confidence (%)") is not None else None
        upvotes = int(row.get("Upvotes") or 0)
        latitude = float(row["Latitude"]) if row.get("Latitude") not in (None, "") else None
        longitude = float(row["Longitude"]) if row.get("Longitude") not in (None, "") else None
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: Confidence, Upvotes, and coordinates must be numeric") from exc
    if (latitude is None) != (longitude is None):
        raise ValueError(f"Row {row_number}: Latitude and Longitude must both be provided")
    if latitude is not None and not -90 <= latitude <= 90:
        raise ValueError(f"Row {row_number}: Latitude is out of range")
    if longitude is not None and not -180 <= longitude <= 180:
        raise ValueError(f"Row {row_number}: Longitude is out of range")

    return {
        "complaint_type": complaint_type,
        "description": text_value(row.get("Description")),
        "image_path": None,
        "city": text_value(row.get("Area / Ward")),
        "location": text_value(row.get("Location / Landmark")),
        "category": category,
        "confidence": confidence,
        "priority": priority,
        "status": status,
        "is_fake": bool_value(row.get("Fake?")),
        "citizen_name": text_value(row.get("Citizen Name")),
        "citizen_email": text_value(row.get("Citizen Email")),
        "created_at": created_at_value(row.get("Filed On")),
        "upvotes": upvotes,
        "latitude": latitude,
        "longitude": longitude,
    }


def complaint_key(complaint):
    return tuple(
        complaint[field]
        for field in (
            "complaint_type",
            "description",
            "city",
            "location",
            "category",
            "confidence",
            "priority",
            "status",
            "is_fake",
            "upvotes",
            "citizen_name",
            "citizen_email",
            "created_at",
        )
    )


def import_workbook(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Workbook not found: {path}")

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if "Complaints" not in workbook.sheetnames:
            raise ValueError("Workbook must contain a 'Complaints' worksheet")
        sheet = workbook["Complaints"]
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows, None)
        if not headers:
            raise ValueError("The Complaints worksheet is empty")
        headers = [str(header).strip() if header is not None else "" for header in headers]
        missing = REQUIRED_HEADERS.difference(headers)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

        complaints = []
        for row_number, values in enumerate(rows, start=2):
            if not any(value is not None for value in values):
                continue
            complaints.append(parse_row(dict(zip(headers, values)), row_number))
    finally:
        workbook.close()

    db.init_db()
    existing = db.get_all_complaints(sort_by="newest")
    existing_keys = {complaint_key(dict(row)) for row in existing}
    imported = 0
    skipped = 0
    for complaint in complaints:
        key = complaint_key(complaint)
        if key in existing_keys:
            skipped += 1
            continue
        db.import_complaint(**complaint)
        existing_keys.add(key)
        imported += 1

    return imported, skipped


if __name__ == "__main__":
    workbook_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WORKBOOK
    imported, skipped = import_workbook(workbook_path)
    print(f"Imported {imported} complaints; skipped {skipped} existing duplicates.")
    print(f"Total complaints in database: {len(db.get_all_complaints())}")
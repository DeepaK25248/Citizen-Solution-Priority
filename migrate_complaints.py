import os
import sys
from datetime import date, datetime
from zipfile import BadZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

import database as db


HEADERS = [
    "Source ID",
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
    "Filed On",
]
DEFAULT_EXPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laptop_complaints_migration.xlsx")
VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_STATUSES = {"Pending", "Processing", "Solved"}
LIVE_EXPORT_HEADERS = {
    "ID",
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
    "Filed On",
}


def _write_redacted_workbook(records, path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Complaints"
    sheet.append(HEADERS)
    for record in records:
        sheet.append([record[field] for field in HEADERS])
    workbook.save(path)


def export_redacted_workbook(path):
    db.init_db()
    complaints = db.get_all_complaints(sort_by="newest")
    records = []
    for complaint in complaints:
        records.append({
            "Source ID": f"laptop:{complaint['id']}",
            "Priority": complaint["priority"],
            "Upvotes": complaint["upvotes"],
            "Category": complaint["category"],
            "Status": complaint["status"],
            "Type": "Photo" if complaint["complaint_type"] == "image" else "Text",
            "Description": complaint["description"] or ("Photo complaint" if complaint["image_path"] else ""),
            "Area / Ward": complaint["city"] or "",
            "Location / Landmark": complaint["location"] or "",
            "Confidence (%)": complaint["confidence"],
            "Fake?": "Yes" if complaint["is_fake"] else "No",
            "Filed On": complaint["created_at"],
        })

    _write_redacted_workbook(records, path)
    return len(complaints)


def _cell_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _created_at(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d 00:00")
    result = _cell_text(value)
    if not result:
        raise ValueError("Filed On is required")
    return result


def _parse_complaint(row, row_number):
    source_id = _cell_text(row.get("Source ID"))
    if not source_id or len(source_id) > 80:
        raise ValueError(f"Row {row_number}: Source ID is missing or too long")

    category = _cell_text(row.get("Category"))
    priority = _cell_text(row.get("Priority"))
    status = _cell_text(row.get("Status"))
    if not category or priority not in VALID_PRIORITIES or status not in VALID_STATUSES:
        raise ValueError(f"Row {row_number}: Category, Priority, or Status is invalid")

    raw_type = (_cell_text(row.get("Type")) or "").casefold()
    complaint_type = "image" if raw_type in {"photo", "image"} else "text"
    try:
        confidence = float(row["Confidence (%)"]) if row.get("Confidence (%)") not in (None, "") else None
        upvotes = int(row.get("Upvotes") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: Confidence or Upvotes is not numeric") from exc
    if confidence is not None and not 0 <= confidence <= 100:
        raise ValueError(f"Row {row_number}: Confidence must be between 0 and 100")
    if upvotes < 0:
        raise ValueError(f"Row {row_number}: Upvotes cannot be negative")

    fake_value = str(row.get("Fake?") or "").strip().casefold()
    return {
        "migration_source_id": source_id,
        "complaint_type": complaint_type,
        "description": _cell_text(row.get("Description")),
        "city": _cell_text(row.get("Area / Ward")),
        "location": _cell_text(row.get("Location / Landmark")),
        "category": category,
        "confidence": confidence,
        "priority": priority,
        "status": status,
        "is_fake": fake_value in {"yes", "true", "1"},
        "upvotes": upvotes,
        "created_at": _created_at(row.get("Filed On")),
    }


def import_redacted_workbook(path):
    if isinstance(path, (str, os.PathLike)) and not os.path.isfile(path):
        raise FileNotFoundError(f"Workbook not found: {path}")

    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException) as exc:
        raise ValueError("The uploaded file is not a valid Excel workbook.") from exc
    try:
        if "Complaints" not in workbook.sheetnames:
            raise ValueError("Workbook must contain a 'Complaints' worksheet")
        rows = workbook["Complaints"].iter_rows(values_only=True)
        header_row = next(rows, None)
        if not header_row:
            raise ValueError("The Complaints worksheet is empty")
        headers = [_cell_text(value) or "" for value in header_row]
        if headers != HEADERS:
            raise ValueError("This must be the redacted workbook generated by migrate_complaints.py export.")

        records = []
        for row_number, values in enumerate(rows, start=2):
            if any(value is not None for value in values):
                records.append(_parse_complaint(dict(zip(headers, values)), row_number))
    finally:
        workbook.close()

    db.init_db()
    return db.merge_migrated_complaints(records)


def convert_render_export(path, output_path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Render export not found: {path}")

    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException) as exc:
        raise ValueError("The Render export is not a valid Excel workbook.") from exc
    try:
        if "Complaints" not in workbook.sheetnames:
            raise ValueError("The Render export must contain a 'Complaints' worksheet")
        rows = workbook["Complaints"].iter_rows(values_only=True)
        header_row = next(rows, None)
        if not header_row:
            raise ValueError("The Render export worksheet is empty")
        headers = [_cell_text(value) or "" for value in header_row]
        missing = LIVE_EXPORT_HEADERS.difference(headers)
        if missing:
            raise ValueError("Render export is missing columns: " + ", ".join(sorted(missing)))

        records = []
        for row_number, values in enumerate(rows, start=2):
            if not any(value is not None for value in values):
                continue
            row = dict(zip(headers, values))
            raw_id = _cell_text(row.get("ID"))
            if not raw_id:
                raise ValueError(f"Row {row_number}: Render complaint ID is missing")
            safe_row = {
                "Source ID": f"render:{raw_id}",
                "Priority": row.get("Priority"),
                "Upvotes": row.get("Upvotes"),
                "Category": row.get("Category"),
                "Status": row.get("Status"),
                "Type": row.get("Type"),
                "Description": row.get("Description"),
                "Area / Ward": row.get("Area / Ward"),
                "Location / Landmark": row.get("Location / Landmark"),
                "Confidence (%)": row.get("Confidence (%)"),
                "Fake?": row.get("Fake?"),
                "Filed On": row.get("Filed On"),
            }
            record = _parse_complaint(safe_row, row_number)
            records.append({
                "Source ID": record["migration_source_id"],
                "Priority": record["priority"],
                "Upvotes": record["upvotes"],
                "Category": record["category"],
                "Status": record["status"],
                "Type": "Photo" if record["complaint_type"] == "image" else "Text",
                "Description": record["description"] or "",
                "Area / Ward": record["city"] or "",
                "Location / Landmark": record["location"] or "",
                "Confidence (%)": record["confidence"],
                "Fake?": "Yes" if record["is_fake"] else "No",
                "Filed On": record["created_at"],
            })
    finally:
        workbook.close()

    _write_redacted_workbook(records, output_path)
    return len(records)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "export":
        count = export_redacted_workbook(DEFAULT_EXPORT)
        print(f"Exported {count} redacted complaints to {DEFAULT_EXPORT}")
    elif len(sys.argv) == 3 and sys.argv[1] == "import":
        imported, skipped = import_redacted_workbook(sys.argv[2])
        print(f"Imported {imported} complaints; skipped {skipped} already-migrated records.")
    elif len(sys.argv) == 4 and sys.argv[1] == "convert-render-export":
        count = convert_render_export(sys.argv[2], sys.argv[3])
        print(f"Converted {count} Render complaints to a redacted migration workbook.")
    else:
        raise SystemExit(
            "Usage: python migrate_complaints.py export | "
            "convert-render-export <render-export.xlsx> <redacted-output.xlsx> | "
            "import <redacted-workbook.xlsx>"
        )

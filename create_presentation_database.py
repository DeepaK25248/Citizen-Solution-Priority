"""Create an isolated SQLite presentation database from a complaint workbook."""

import argparse
from datetime import date, datetime
import os
from pathlib import Path
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

import database as db


REQUIRED_HEADERS = {
    "ID", "Priority", "Upvotes", "Category", "Status", "Type", "Description",
    "Area / Ward", "Location / Landmark", "Confidence (%)", "Fake?",
    "Citizen Name", "Citizen Email", "Filed On",
}
VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_STATUSES = {"Pending", "Processing", "Solved"}


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _filed_on(value, row_number):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d 00:00")
    value = _text(value)
    if not value:
        raise ValueError(f"Row {row_number}: Filed On is required")
    return value


def read_complaints(workbook_path):
    try:
        workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    except (BadZipFile, OSError, InvalidFileException) as exc:
        raise ValueError("Could not open the supplied .xlsx workbook.") from exc

    try:
        if "Complaints" not in workbook.sheetnames:
            raise ValueError("Workbook must contain a 'Complaints' worksheet.")
        rows = workbook["Complaints"].iter_rows(values_only=True)
        raw_headers = next(rows, None)
        if not raw_headers:
            raise ValueError("The Complaints worksheet is empty.")
        headers = [_text(value) for value in raw_headers]
        missing_headers = REQUIRED_HEADERS.difference(headers)
        if missing_headers:
            raise ValueError(
                "Missing required columns: " + ", ".join(sorted(missing_headers))
            )

        records = []
        seen_ids = set()
        for row_number, values in enumerate(rows, start=2):
            if not any(value is not None for value in values):
                continue
            row = dict(zip(headers, values))
            source_id = _text(row.get("ID")) or str(row_number)
            if source_id in seen_ids:
                raise ValueError(f"Row {row_number}: duplicate ID")
            seen_ids.add(source_id)

            priority = _text(row.get("Priority"))
            status = _text(row.get("Status"))
            category = _text(row.get("Category"))
            description = _text(row.get("Description"))
            if priority not in VALID_PRIORITIES or status not in VALID_STATUSES:
                raise ValueError(f"Row {row_number}: invalid Priority or Status")
            if not category or not description:
                raise ValueError(f"Row {row_number}: Category and Description are required")

            try:
                upvotes = int(row.get("Upvotes") or 0)
                confidence = (
                    float(row["Confidence (%)"])
                    if row.get("Confidence (%)") not in (None, "")
                    else None
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Row {row_number}: invalid Upvotes or Confidence") from exc
            if upvotes < 0:
                raise ValueError(f"Row {row_number}: Upvotes cannot be negative")
            if confidence is not None and not 0 <= confidence <= 100:
                raise ValueError(f"Row {row_number}: Confidence must be 0-100")

            fake_value = _text(row.get("Fake?")).casefold()
            complaint_type = _text(row.get("Type")).casefold()
            records.append({
                "demo_key": f"presentation-workbook-{source_id}",
                "complaint_type": "image" if complaint_type in {"photo", "image"} else "text",
                "description": description,
                "city": _text(row.get("Area / Ward")),
                "location": _text(row.get("Location / Landmark")),
                "category": category,
                "confidence": confidence,
                "priority": priority,
                "status": status,
                "is_fake": fake_value in {"yes", "true", "1"},
                "upvotes": upvotes,
                "citizen_name": "Project Sample",
                "citizen_email": None,
                "created_at": _filed_on(row.get("Filed On"), row_number),
            })
        if not records:
            raise ValueError("The workbook contains no complaint records.")
        return records
    finally:
        workbook.close()


def create_database(workbook_path, database_path):
    workbook_path = Path(workbook_path).resolve()
    database_path = Path(database_path).resolve()
    if workbook_path == database_path:
        raise ValueError("The output database path cannot be the workbook path.")
    if database_path.exists():
        raise FileExistsError(
            f"{database_path} already exists; move it or choose a new output path."
        )

    records = read_complaints(workbook_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    db.USE_POSTGRES = False
    db.DB_PATH = str(database_path)
    db.init_db()
    db.import_demo_complaints(records)
    imported = db.count_demo_complaints()
    if imported != len(records):
        raise RuntimeError(
            f"Expected {len(records)} records in the presentation database, found {imported}."
        )
    return imported


def main():
    parser = argparse.ArgumentParser(
        description="Build a separate, local-only SQLite database for project demos."
    )
    parser.add_argument("workbook", help="Path to citysolution_complaints.xlsx")
    parser.add_argument(
        "--database",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "citysolution_presentation.db"),
        help="New SQLite output path (must not already exist)",
    )
    args = parser.parse_args()
    count = create_database(args.workbook, args.database)
    print(f"Created {count} project sample complaints in: {Path(args.database).resolve()}")
    print("No existing app database was changed; email notifications are disabled for these records.")


if __name__ == "__main__":
    main()

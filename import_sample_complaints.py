"""
Loads the sample complaints (data/sample_citizen_complaints.xlsx, built by
generate_sample_complaints_excel.py) into the app's own database
(citysolution.db), so they show up in /complaints and /dashboard exactly
like real citizen-submitted complaints - including their priority,
upvotes, status, and citizen details.

Run this once after setting up the project if you want the app to start
pre-populated instead of empty:

    python import_sample_complaints.py

Safe to run multiple times - it always regenerates the sheet from
data/bengaluru_complaints.csv (via generate_sample_complaints_excel) and
appends a fresh batch of imported rows; existing complaints are never
deleted or duplicated-checked, so run init_db() once per fresh database.
"""

import database as db
from generate_sample_complaints_excel import build_sample_rows, write_workbook


def import_rows(rows):
    db.init_db()
    imported = 0
    for r in rows:
        db.import_complaint(
            complaint_type="text",
            description=r["description"],
            image_path=None,
            city=r["area"],
            location=r["location"],
            category=r["category"],
            confidence=r["confidence"],
            priority=r["priority"],
            status=r["status"],
            is_fake=r["is_fake"],
            citizen_name=r["citizen_name"],
            citizen_email=r["citizen_email"],
            created_at=r["filed_on"],
            upvotes=r["upvotes"],
        )
        imported += 1
    return imported


if __name__ == "__main__":
    rows = build_sample_rows(n=250)
    write_workbook(rows)  # keep the .xlsx in sync with what gets imported
    count = import_rows(rows)
    print(f"Imported {count} sample complaints into citysolution.db")
    print("Start the app (python app.py) and open /complaints or /dashboard to see them.")

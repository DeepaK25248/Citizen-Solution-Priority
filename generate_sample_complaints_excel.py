"""
Builds a filled-in Excel workbook of realistic citizen complaints, using
sentences from data/bengaluru_complaints.csv (real BBMP categories + real
Bengaluru localities), classified through the app's own text_classifier
and priority modules so the sheet matches exactly what /export produces
inside the running app.

This is a standalone script for producing a demo/sample workbook - the
live app's /export route builds the same kind of sheet from whatever
citizens have actually submitted through the form.
"""

import csv
import random
from datetime import datetime, timedelta

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from text_classifier import classify_text
from priority import score_priority
from generate_bengaluru_dataset import WARDS as AREAS, LOCATION_PHRASES as ROADS

random.seed(7)

FIRST_NAMES = [
    "Anitha", "Rahul", "Priya", "Suresh", "Divya", "Karthik", "Meera", "Arjun",
    "Lakshmi", "Vikram", "Sneha", "Manoj", "Deepa", "Ravi", "Pooja", "Nikhil",
    "Sowmya", "Ashwin", "Kavya", "Ramesh", "Shruti", "Sanjay", "Anusha", "Praveen",
]
LAST_NAMES = [
    "Rao", "Kumar", "Reddy", "Gowda", "Shetty", "Iyer", "Naidu", "Murthy",
    "Sharma", "Nair", "Menon", "Pillai", "Bhat", "Prabhu", "Hegde",
]
STATUSES = ["Pending", "Pending", "Processing", "Processing", "Solved"]  # weighted
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com"]


def load_dataset(path="data/bengaluru_complaints.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_sample_rows(n=250):
    dataset = load_dataset()
    sample = random.sample(dataset, n)

    rows = []
    now = datetime.now()
    for i, item in enumerate(sample, start=1):
        text = item["text"]
        category, confidence = classify_text(text)
        priority = score_priority(category, text)
        status = random.choice(STATUSES)
        is_fake = random.random() < 0.03  # ~3% flagged fake, like a real queue

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = f"{name.split()[0].lower()}.{name.split()[1].lower()}@{random.choice(DOMAINS)}"

        # Extract an area name mention from the text where possible, else blank
        filed_days_ago = random.randint(0, 45)
        filed_on = (now - timedelta(days=filed_days_ago, hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M")

        # Upvotes: most complaints get a handful, some widely-shared ones get a
        # lot - enough to demonstrate the upvote -> priority escalation in the
        # app (see priority.effective_priority) once imported.
        upvotes = max(0, int(random.gauss(6, 8)))
        if random.random() < 0.06:  # a few "viral" complaints
            upvotes += random.randint(20, 45)

        rows.append({
            "id": i,
            "priority": priority,
            "category": category,
            "status": status,
            "type": "Text",
            "description": text,
            "confidence": confidence,
            "is_fake": is_fake,
            "upvotes": upvotes,
            "citizen_name": name,
            "citizen_email": email,
            "filed_on": filed_on,
            "area": random.choice(AREAS),
            "location": random.choice(ROADS),
        })

    # Sort like the dashboard does: High priority first, then most upvoted, then newest
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    rows.sort(key=lambda r: (priority_order[r["priority"]], -r["upvotes"], -r["id"]))
    for i, r in enumerate(rows, start=1):
        r["id"] = i
    return rows


def write_workbook(rows, out_path="data/sample_citizen_complaints.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Complaints"

    headers = [
        "ID", "Priority", "Upvotes", "Category", "Status", "Type", "Description",
        "Area / Ward", "Location / Landmark", "Confidence (%)", "Fake?",
        "Citizen Name", "Citizen Email", "Filed On", "Latitude", "Longitude",
    ]
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="12233A", end_color="12233A", fill_type="solid")
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"

    body_font = Font(name="Arial")
    priority_fills = {
        "High": PatternFill(start_color="F8ECEB", end_color="F8ECEB", fill_type="solid"),
        "Medium": PatternFill(start_color="FBF0DE", end_color="FBF0DE", fill_type="solid"),
        "Low": PatternFill(start_color="EEF0E9", end_color="EEF0E9", fill_type="solid"),
    }

    for row_idx, r in enumerate(rows, start=2):
        values = [
            r["id"], r["priority"], r["upvotes"], r["category"], r["status"], r["type"],
            r["description"], r["area"], r["location"], r["confidence"],
            "Yes" if r["is_fake"] else "No",
            r["citizen_name"], r["citizen_email"], r["filed_on"],
            r.get("latitude"), r.get("longitude"),
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = body_font
            cell.alignment = Alignment(vertical="top", wrap_text=(col_idx == 7))
        fill = priority_fills.get(r["priority"])
        if fill:
            ws.cell(row=row_idx, column=2).fill = fill

    widths = [6, 10, 9, 22, 12, 8, 60, 16, 20, 14, 7, 18, 26, 16, 12, 12]
    for col_idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Auto-filter for sorting/filtering in Excel
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"

    wb.save(out_path)
    return out_path


if __name__ == "__main__":
    rows = build_sample_rows(n=250)
    path = write_workbook(rows)
    print(f"Wrote {len(rows)} sample complaints to {path}")

    from collections import Counter
    print("By category:", Counter(r["category"] for r in rows))
    print("By priority:", Counter(r["priority"] for r in rows))
    print("By status:", Counter(r["status"] for r in rows))

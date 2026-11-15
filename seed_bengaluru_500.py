"""Replace app complaints and an Excel workbook with 500 Bengaluru samples."""

import os
import sys
import tempfile

import database as db
from generate_bengaluru_dataset import WARDS
from generate_sample_complaints_excel import build_sample_rows, write_workbook
from text_classifier import _TRAIN_SIZE


DEFAULT_WORKBOOK = r"C:\Users\Rashmi\Downloads\citysolution_complaints.xlsx"
CATEGORY_PHOTOS = {
    "Road Maintenance": "category_photos/road-maintenance.jpg",
    "Storm Water Drain": "category_photos/storm-water-drain.jpg",
    "Solid Waste": "category_photos/solid-waste.jpg",
    "Street Light / Electrical": "category_photos/street-light-electrical.jpg",
    "Water Supply": "category_photos/water-supply.jpg",
    "Sewage / Sanitation": "category_photos/sewage-sanitation.jpg",
    "Stray Animals": "category_photos/stray-animals.jpg",
    "Parks & Trees": "category_photos/parks-trees.jpg",
    "Encroachment": "category_photos/encroachment.jpg",
    "Others": "category_photos/others.jpg",
}


def seed(workbook_path=DEFAULT_WORKBOOK):
    rows = build_sample_rows(n=500)
    bengaluru_wards = set(WARDS)
    if len(rows) != 500 or any(row["area"] not in bengaluru_wards for row in rows):
        raise ValueError("Generated complaints must be exactly 500 Bengaluru records")

    workbook_path = os.path.abspath(workbook_path)
    output_directory = os.path.dirname(workbook_path)
    os.makedirs(output_directory, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".xlsx", prefix="citysolution_", dir=output_directory, delete=False
    )
    temp_path = temp_file.name
    temp_file.close()

    complaints = [{
        "id": row["id"],
        "complaint_type": "text",
        "description": row["description"],
        "image_path": CATEGORY_PHOTOS.get(row["category"]),
        "city": row["area"],
        "location": row["location"],
        "category": row["category"],
        "confidence": row["confidence"],
        "priority": row["priority"],
        "status": row["status"],
        "is_fake": row["is_fake"],
        "upvotes": row["upvotes"],
        "citizen_name": row["citizen_name"],
        "citizen_email": row["citizen_email"],
        "created_at": row["filed_on"],
    } for row in rows]

    try:
        write_workbook(rows, out_path=temp_path)
        db.init_db()
        db.replace_complaints(complaints)
        os.replace(temp_path, workbook_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return len(rows), workbook_path


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WORKBOOK
    count, path = seed(target)
    print(f"Replaced app complaints with {count} Bengaluru records.")
    print(f"Classifier trained on {_TRAIN_SIZE} Bengaluru dataset rows.")
    print(f"Workbook written to: {path}")
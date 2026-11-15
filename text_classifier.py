"""
Text complaint classifier.

Pipeline mirrors "NLP based Model for Classification of Complaints"
(Qurat-ul-ain et al., 2022): lowercase -> remove stopwords -> TF-IDF
vectorize -> classify with Logistic Regression.

Trained on data/bengaluru_complaints.csv - 1,700+ labeled complaint
sentences generated from BBMP's real grievance category taxonomy
(Road Maintenance, Storm Water Drain, Solid Waste, Street Light /
Electrical, Water Supply, Sewage / Sanitation, Stray Animals, Parks &
Trees, Encroachment, Others) combined with real Bengaluru ward/locality
names. See generate_bengaluru_dataset.py for how it was built and why
(no network access here to pull a real free-text complaints export).

To retrain on a different or real dataset: replace
data/bengaluru_complaints.csv with your own file (columns: text,category)
and restart the app - it retrains automatically at import time.
"""

import csv
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

_HERE = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(_HERE, "data", "bengaluru_complaints.csv")

CATEGORIES = [
    "Road Maintenance",
    "Storm Water Drain",
    "Solid Waste",
    "Street Light / Electrical",
    "Water Supply",
    "Sewage / Sanitation",
    "Stray Animals",
    "Parks & Trees",
    "Encroachment",
    "Others",
]

# Small fallback used only if the CSV is missing (e.g. before
# generate_bengaluru_dataset.py has been run).
_FALLBACK_SEED = [
    ("There is a large pothole on the main road that is damaging vehicles.", "Road Maintenance"),
    ("The storm water drain near my house is overflowing onto the road.", "Storm Water Drain"),
    ("Garbage has not been collected from our street for over a week.", "Solid Waste"),
    ("The street light has not worked for over a month.", "Street Light / Electrical"),
    ("There has been no water supply to our area for three days.", "Water Supply"),
    ("The sewage line near our house is overflowing onto the street.", "Sewage / Sanitation"),
    ("A pack of stray dogs has been chasing pedestrians near our lane.", "Stray Animals"),
    ("A large tree branch is at risk of falling onto the road.", "Parks & Trees"),
    ("A shop has illegally encroached onto the footpath.", "Encroachment"),
    ("This is a general inquiry about ward office working hours.", "Others"),
]


def _load_dataset():
    if os.path.exists(DATASET_PATH):
        rows = []
        with open(DATASET_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = (row.get("text") or "").strip()
                category = (row.get("category") or "").strip()
                if text and category:
                    rows.append((text, category))
        if rows:
            return rows
    return _FALLBACK_SEED


def _build_and_train():
    data = _load_dataset()
    texts = [t for t, _ in data]
    labels = [l for _, l in data]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(max_iter=2000, C=6.0, class_weight="balanced")),
    ])
    pipeline.fit(texts, labels)
    return pipeline, len(data)


_MODEL, _TRAIN_SIZE = _build_and_train()


def classify_text_scores(text: str):
    """Return native-float confidence scores for every text category."""
    text = (text or "").strip()
    if not text:
        return {"Others": 100.0}

    proba = _MODEL.predict_proba([text])[0]
    classes = _MODEL.classes_
    return {str(category): float(confidence * 100) for category, confidence in zip(classes, proba)}


def classify_text(text: str):
    """Return (category, confidence) for a complaint description."""
    scores = classify_text_scores(text)
    category = max(scores, key=scores.get)
    return category, float(round(scores[category], 1))


if __name__ == "__main__":
    print(f"Trained on {_TRAIN_SIZE} rows from {DATASET_PATH}")
    tests = [
        "There is a big pothole on 100 Feet Road in Indiranagar",
        "No water supply in HSR Layout for three days",
        "Garbage has not been collected in Koramangala for a week",
        "Stray dogs are chasing people near the park in Jayanagar",
        "Street lights have not worked in our lane for a month",
    ]
    for t in tests:
        print(t, "->", classify_text(t))

"""Combine text and image model scores for a civic complaint."""

from image_classifier import classify_image_scores
from text_classifier import classify_text_scores


IMAGE_WEIGHT = 0.8
TEXT_WEIGHT = 1 - IMAGE_WEIGHT


def classify_complaint(description, image_path=None):
    description = (description or "").strip()
    if image_path and description:
        image_scores = classify_image_scores(image_path)
        text_scores = classify_text_scores(description)
        categories = set(image_scores) | set(text_scores)
        combined_scores = {
            category: IMAGE_WEIGHT * image_scores.get(category, 0.0)
            + TEXT_WEIGHT * text_scores.get(category, 0.0)
            for category in categories
        }
        category = max(combined_scores, key=combined_scores.get)
        return category, float(round(combined_scores[category], 1)), "image and description"

    if image_path:
        scores = classify_image_scores(image_path)
        category = max(scores, key=scores.get)
        return category, float(round(scores[category], 1)), "image"

    scores = classify_text_scores(description)
    category = max(scores, key=scores.get)
    return category, float(round(scores[category], 1)), "description"
"""
Image complaint classifier.

Paper 2 ("CitySolution") trains a real CNN (MobileNets + transfer learning)
on Google's Teachable Machine using 5,494 labeled photos across four
classes: Damaged Road, Flood, Trash, Homeless People.

This demo environment has no camera-collected training set and no GPU/
Teachable Machine access, so this module uses a lightweight heuristic
(average color + edge density) as a stand-in classifier so the end-to-end
flow can be demonstrated. Swap `classify_image()` for a call to a real
exported .tflite / Teachable Machine model in production, exactly as
described in the paper.
"""

import numpy as np
from PIL import Image, ImageFilter

IMAGE_CATEGORIES = ["Road Maintenance", "Storm Water Drain", "Solid Waste", "Stray Animals"]


def _edge_density(gray_img: Image.Image) -> float:
    edges = gray_img.filter(ImageFilter.FIND_EDGES)
    arr = np.asarray(edges, dtype=np.float32)
    return float(arr.mean()) / 255.0


def classify_image_scores(image_path: str):
    """Return native-float confidence scores for the image categories.

    This is a placeholder for the trained MobileNets/CNN model from the
    paper - see module docstring.
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception:
        return {"Others": 100.0}

    img = img.resize((128, 128))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    r = float(arr[:, :, 0].mean())
    g = float(arr[:, :, 1].mean())
    b = float(arr[:, :, 2].mean())
    brightness = (r + g + b) / 3
    gray = img.convert("L")
    edges = _edge_density(gray)
    saturation = arr.max(axis=2) - arr.min(axis=2)
    blue_water = float(((arr[:, :, 2] > arr[:, :, 0] * 1.08) & (arr[:, :, 2] > arr[:, :, 1] * 0.92)).mean())
    bright_reflections = float(((arr.max(axis=2) > 0.58) & (saturation < 0.20)).mean())

    scores = {
        # Water can be muddy brown; include blue spray and bright reflections,
        # not only the image-wide average color.
        "Storm Water Drain": max(0.0, (0.5 - edges) * 0.5 + blue_water * 2.0 + bright_reflections * 0.6),
        # Solid Waste: greenish/brownish clutter, high edge density
        "Solid Waste": max(0.0, (g - b) * 0.5 + edges),
        # Road Maintenance: grey, high edge density (cracks/potholes), low saturation
        "Road Maintenance": max(0.0, (1 - abs(r - g) - abs(g - b)) * edges * 1.5),
        # Color and edge density cannot reliably identify an animal, so this
        # is only a weak fallback until a trained object model is available.
        "Stray Animals": max(0.0, 1 - brightness) * 0.08,
    }

    total = sum(scores.values()) or 1.0
    return {category: float(score / total * 100) for category, score in scores.items()}


def classify_image(image_path: str):
    """Return (category, confidence) using simple color/texture heuristics."""
    scores = classify_image_scores(image_path)
    category = max(scores, key=scores.get)
    return category, float(round(scores[category], 1))

"""Outfit compatibility classification for Milestone 6.

The module first looks for local Polyvore-style metadata.  If no usable dataset
is present, it deliberately trains and labels a clearly marked fallback model
from documented sample clothing combinations rather than pretending to use
Polyvore.
"""

from __future__ import annotations

import csv
import json
import random
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from src.config import BASE_DIR


MODEL_PATH = BASE_DIR / "models" / "compatibility_model.joblib"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

CATEGORY_NAMES = (
    "t-shirt", "shirt", "hoodie", "sweater", "jacket", "coat", "top", "blouse",
    "pants", "jeans", "trousers", "shorts", "skirt", "leggings",
    "dress", "jumpsuit", "overall", "onesie",
    "shoes", "sneakers", "boots", "sandals", "heels",
    "bag", "hat", "scarf", "watch", "glasses",
)
UPPER = {"t-shirt", "shirt", "hoodie", "sweater", "jacket", "coat", "top", "blouse"}
LOWER = {"pants", "jeans", "trousers", "shorts", "skirt", "leggings"}
SHOES = {"shoes", "sneakers", "boots", "sandals", "heels"}


def _category(item: Dict[str, Any]) -> str:
    return str(item.get("category", item.get("category_name", ""))).strip().lower()


def _hex_rgb(value: Any) -> Optional[np.ndarray]:
    if not value:
        return None
    text = str(value).strip().lstrip("#")
    if len(text) != 6:
        return None
    try:
        return np.array([int(text[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)
    except ValueError:
        return None


def _color_distance(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    first_rgb = _hex_rgb(first.get("dominant_color"))
    second_rgb = _hex_rgb(second.get("dominant_color"))
    if first_rgb is None or second_rgb is None:
        return 0.5
    distance = float(np.linalg.norm(first_rgb - second_rgb))
    return float(np.clip(distance / 441.672956, 0.0, 1.0))


def _embedding_similarity(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    values = []
    for item in (first, second):
        raw = item.get("embedding_json")
        if raw:
            try:
                values.append(np.asarray(json.loads(raw), dtype=float).reshape(-1))
                continue
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        values.append(np.array([0.0]))

    first_vector = values[0]
    second_vector = values[1]
    size = max(first_vector.size, second_vector.size)
    first_vector = np.pad(first_vector, (0, size - first_vector.size))
    second_vector = np.pad(second_vector, (0, size - second_vector.size))
    if size == 0 or not np.any(first_vector) or not np.any(second_vector):
        return 0.5
    denominator = float(np.linalg.norm(first_vector) * np.linalg.norm(second_vector))
    if denominator == 0:
        return 0.5
    cosine = float(np.dot(first_vector, second_vector) / denominator)
    return float(np.clip((cosine + 1.0) / 2.0, 0.0, 1.0))


def extract_combination_features(items: Sequence[Dict[str, Any]]) -> np.ndarray:
    """Convert an outfit into a fixed-length numeric feature vector."""
    outfit = [dict(item) for item in items if isinstance(item, dict)]
    category_counts = np.zeros(len(CATEGORY_NAMES), dtype=float)
    for item in outfit:
        category = _category(item)
        if category in CATEGORY_NAMES:
            category_counts[CATEGORY_NAMES.index(category)] += 1.0
    if outfit:
        category_counts /= float(len(outfit))

    pairs = list(combinations(outfit, 2))
    if pairs:
        color_distances = [_color_distance(a, b) for a, b in pairs]
        embedding_scores = [_embedding_similarity(a, b) for a, b in pairs]
        compatible_categories = sum(
            1.0 if { _category(a), _category(b) }.issubset(UPPER | LOWER)
            or _category(a) in SHOES or _category(b) in SHOES
            else 0.0
            for a, b in pairs
        ) / len(pairs)
        mean_color_distance = float(np.mean(color_distances))
        mean_embedding_similarity = float(np.mean(embedding_scores))
    else:
        compatible_categories = 0.5
        mean_color_distance = 0.5
        mean_embedding_similarity = 0.5

    fabrics = [str(item.get("fabric", "")).strip().lower() for item in outfit if item.get("fabric")]
    fabric_agreement = 1.0 if len(set(fabrics)) <= 1 and fabrics else 0.5

    seasons = [str(item.get("season", "")).strip().lower() for item in outfit if item.get("season")]
    season_agreement = 1.0 if len(set(seasons)) <= 1 and seasons else 0.5

    occasions = [str(item.get("occasion", "")).strip().lower() for item in outfit if item.get("occasion")]
    occasion_consistency = 1.0 if len(set(occasions)) <= 1 and occasions else 0.5

    numerical = np.array([
        float(len(outfit)), mean_color_distance, mean_embedding_similarity,
        compatible_categories, fabric_agreement, season_agreement, occasion_consistency,
    ], dtype=float)
    return np.concatenate([category_counts, numerical])


# Backwards-friendly public alias.
extract_features = extract_combination_features


def _fallback_positive_outfits() -> List[List[Dict[str, Any]]]:
    """Create documented sample positive outfits for use only without Polyvore."""
    examples = [
        [("White Shirt", "shirt", "#FFFFFF"), ("Blue Jeans", "jeans", "#336699")],
        [("Black Shirt", "shirt", "#111111"), ("Beige Pants", "pants", "#C8B79B")],
        [("Blue T-Shirt", "t-shirt", "#336699"), ("Black Shorts", "shorts", "#111111")],
        [("Grey Hoodie", "hoodie", "#777777"), ("Navy Pants", "pants", "#000080")],
        [("White Blouse", "blouse", "#FFFFFF"), ("Black Skirt", "skirt", "#111111")],
        [("Green Sweater", "sweater", "#228B22"), ("Beige Skirt", "skirt", "#C8B79B")],
        [("Blue Dress", "dress", "#336699"), ("White Sneakers", "sneakers", "#FFFFFF")],
        [("Black Jumpsuit", "jumpsuit", "#111111"), ("Black Boots", "boots", "#111111")],
    ]
    positive: List[List[Dict[str, Any]]] = []
    for outfit in examples:
        items = [{"name": name, "category": category, "dominant_color": color,
                  "fabric": "cotton", "season": "all", "occasion": "casual"}
                 for name, category, color in outfit]
        positive.append(items)

    shoes = ["shoes", "sneakers", "boots"]
    uppers = [("shirt", "#FFFFFF"), ("t-shirt", "#336699"), ("hoodie", "#777777")]
    lowers = [("pants", "#111111"), ("jeans", "#2244AA"), ("skirt", "#C8B79B")]
    for upper, upper_color in uppers:
        for lower, lower_color in lowers:
            positive.append([
                {"category": upper, "dominant_color": upper_color, "fabric": "cotton", "season": "all", "occasion": "casual"},
                {"category": lower, "dominant_color": lower_color, "fabric": "cotton", "season": "all", "occasion": "casual"},
                {"category": shoes[len(positive) % len(shoes)], "dominant_color": "#FFFFFF", "fabric": "leather", "season": "all", "occasion": "casual"},
            ])
    return positive


def generate_negative_examples(positive_outfits: Iterable[Sequence[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
    """Generate unsuitable examples by mixing items across outfit categories."""
    all_items = [dict(item) for outfit in positive_outfits for item in outfit]
    negatives: List[List[Dict[str, Any]]] = []
    if not all_items:
        return negatives

    category_pools: Dict[str, List[Dict[str, Any]]] = {}
    for item in all_items:
        category_pools.setdefault(_category(item), []).append(item)

    for outfit in positive_outfits:
        outfit_categories = {_category(item) for item in outfit}
        unsuitable = [item for item in all_items if _category(item) not in outfit_categories]
        if len(outfit) >= 2 and unsuitable:
            candidate = list(outfit[:1]) + [dict(suitable) for suitable in unsuitable[: max(1, len(outfit) - 1)]]
            candidate[1]["dominant_color"] = "#FF00FF"
            if len(candidate) == len(outfit):
                negatives.append(candidate)

    # Category collisions are also unsuitable examples: top paired with top,
    # dress paired with pants, and random remixes of otherwise valid items.
    for first_category in ("shirt", "hoodie", "dress"):
        first_pool = category_pools.get(first_category) or [{"category": first_category, "dominant_color": "#FFFFFF"}]
        for second_category in ("shirt", "t-shirt", "dress", "pants"):
            if second_category != first_category:
                second_pool = category_pools.get(second_category) or [{"category": second_category, "dominant_color": "#FF00FF"}]
                negatives.append([dict(first_pool[0]), dict(second_pool[0])])
        if first_category != "dress":
            negatives.append([dict(first_pool[0]), dict(first_pool[0]), {"category": "hat", "dominant_color": "#FF00FF"}])

    unique: Dict[str, List[Dict[str, Any]]] = {}
    for outfit in negatives:
        key = json.dumps([(_category(item), item.get("dominant_color")) for item in outfit], sort_keys=True)
        unique[key] = outfit
    return list(unique.values())


def find_polyvore_data(data_dir: Optional[Path] = None) -> Optional[Path]:
    """Return a local JSON/JSONL/CSV metadata file that can represent outfits."""
    directory = Path(data_dir or RAW_DATA_DIR)
    if not directory.exists():
        return None
    for pattern in ("*.json", "*.jsonl", "*.csv"):
        for path in sorted(directory.rglob(pattern)):
            if path.name.lower() in {"compatibility_model_metadata.json", "outfit_metadata.json"}:
                continue
            if path.stat().st_size > 0:
                return path
    return None


def load_polyvore_outfits(path: Optional[Path] = None) -> Optional[List[List[Dict[str, Any]]]]:
    """Load Polyvore-style outfit metadata from a local file when available."""
    source = find_polyvore_data() if path is None else Path(path)
    if source is None or not source.exists():
        return None

    records: List[Any] = []
    try:
        if source.suffix.lower() == ".csv":
            with source.open("r", encoding="utf-8", newline="") as handle:
                records = list(csv.DictReader(handle))
        elif source.suffix.lower() == ".jsonl":
            with source.open("r", encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle if line.strip()]
        else:
            with source.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                records = payload
            elif isinstance(payload, dict):
                records = payload.get("outfits") or payload.get("items") or [payload]
    except (OSError, json.JSONDecodeError, csv.Error):
        return None

    outfits: List[List[Dict[str, Any]]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        raw_items = record.get("items") or record.get("outfit") or record.get("clothing_items")
        if isinstance(raw_items, list):
            items: List[Dict[str, Any]] = []
            for raw in raw_items:
                if isinstance(raw, dict):
                    items.append(raw)
                elif isinstance(raw, str):
                    items.append({"category": raw})
            if len(items) >= 2:
                outfits.append(items)
        elif record.get("category"):
            if record.get("outfit_id") is not None:
                # CSV-style records are grouped by outfit_id below.
                pass

    if source.suffix.lower() == ".csv":
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            outfit_id = str(record.get("outfit_id") or record.get("set_id") or record.get("id") or "")
            if outfit_id:
                grouped.setdefault(outfit_id, []).append(record)
        outfits = [items for items in grouped.values() if len(items) >= 2]

    return outfits or None


def prepare_training_data(polyvore_path: Optional[Path] = None) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Prepare positive and negative combination examples and report provenance."""
    polyvore_outfits = load_polyvore_outfits(polyvore_path)
    if polyvore_outfits:
        positives = polyvore_outfits
        source = str((polyvore_path or find_polyvore_data()) or "")
        dataset_name = "Polyvore"
    else:
        positives = _fallback_positive_outfits()
        source = "built-in sample data"
        dataset_name = "Fallback sample data"

    negatives = generate_negative_examples(positives)
    while len(negatives) < len(positives):
        if not positives:
            break
        shuffled = [dict(item) for item in random.Random(42 + len(negatives)).choice(positives)]
        if shuffled:
            shuffled[-1]["dominant_color"] = "#FF00FF"
            negatives.append(shuffled)

    feature_rows = [extract_combination_features(outfit) for outfit in positives]
    feature_rows += [extract_combination_features(outfit) for outfit in negatives]
    labels = [1] * len(positives) + [0] * len(negatives)
    metadata = {
        "dataset_name": dataset_name,
        "source": source,
        "positive_examples": len(positives),
        "negative_examples": len(negatives),
        "feature_count": len(feature_rows[0]) if feature_rows else 0,
    }
    return np.asarray(feature_rows, dtype=float), np.asarray(labels, dtype=int), metadata


def train_model(polyvore_path: Optional[Path] = None, model_path: Optional[Path] = None) -> Dict[str, Any]:
    """Train, evaluate, and save a real Random Forest compatibility model."""
    X, y, metadata = prepare_training_data(polyvore_path)
    if len(np.unique(y)) < 2:
        raise RuntimeError("Compatibility training requires both positive and negative examples.")

    test_size = 0.25
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if len(np.unique(y_test)) > 1 else None,
    }

    destination = Path(model_path or MODEL_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model, "metadata": metadata, "metrics": metrics}
    joblib.dump(payload, destination)

    return {"model": model, "metrics": metrics, "metadata": metadata, "model_path": str(destination)}


def evaluate_model(model_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the saved artifact and return its recorded evaluation metrics."""
    payload = load_model(model_path)
    if payload is None:
        return {"error": "No trained compatibility model is available."}
    return dict(payload.get("metrics") or {})


def save_model(model: Any, model_path: Optional[Path] = None, metadata: Optional[Dict[str, Any]] = None,
               metrics: Optional[Dict[str, Any]] = None) -> str:
    """Save a fitted model or model payload with Joblib."""
    destination = Path(model_path or MODEL_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = model if isinstance(model, dict) and "model" in model else {
        "model": model, "metadata": metadata or {}, "metrics": metrics or {},
    }
    joblib.dump(payload, destination)
    return str(destination)


def load_model(model_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load a saved compatibility model payload, or return None if invalid."""
    source = Path(model_path or MODEL_PATH)
    if not source.exists():
        return None
    try:
        payload = joblib.load(source)
        if isinstance(payload, dict) and "model" in payload:
            return payload
    except (OSError, ValueError, EOFError, ImportError):
        return None
    return None


def get_model_status(model_path: Optional[Path] = None) -> Dict[str, Any]:
    payload = load_model(model_path)
    if payload is None:
        return {"available": False, "dataset_name": None, "metrics": {}, "source": None}
    metadata = payload.get("metadata") or {}
    return {
        "available": True,
        "dataset_name": metadata.get("dataset_name"),
        "source": metadata.get("source"),
        "positive_examples": metadata.get("positive_examples", 0),
        "negative_examples": metadata.get("negative_examples", 0),
        "metrics": payload.get("metrics") or {},
    }


def predict_compatibility(items: Sequence[Dict[str, Any]], model_path: Optional[Path] = None) -> float:
    """Return the probability that a clothing combination is compatible."""
    payload = load_model(model_path)
    if payload is None:
        payload = train_model(model_path=model_path)
    model = payload["model"]
    features = extract_combination_features(items).reshape(1, -1)
    probability = float(model.predict_proba(features)[0][1])
    return float(np.clip(probability, 0.0, 1.0))


predict_outfit_probability = predict_compatibility
predict_outfit_compatibility = predict_compatibility

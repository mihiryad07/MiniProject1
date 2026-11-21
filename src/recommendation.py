"""Beginner-friendly content-based clothing recommendations."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

from src.feature_extraction import extract_image_features
from src.compatibility_model import predict_compatibility
from src.weather import get_season_for_weather


UPPER_CATEGORIES = {"t-shirt", "shirt", "hoodie", "sweater", "jacket", "top", "blouse"}
LOWER_CATEGORIES = {"pants", "jeans", "trousers", "shorts", "skirt", "leggings"}
SHOE_CATEGORIES = {"shoes", "sneakers", "boots", "sandals"}
COMPLETE_CATEGORIES = {"dress", "jumpsuit", "overall", "onesie"}

COMPATIBLE_CATEGORY_PAIRS = {
    frozenset(("shirt", "pants")), frozenset(("shirt", "jeans")),
    frozenset(("t-shirt", "pants")), frozenset(("t-shirt", "jeans")),
    frozenset(("t-shirt", "shorts")), frozenset(("hoodie", "pants")),
    frozenset(("hoodie", "jeans")), frozenset(("jacket", "dress")),
    frozenset(("sweater", "skirt")), frozenset(("dress", "shoes")),
}


def parse_hex_colour(value: Optional[str]) -> Optional[np.ndarray]:
    """Convert a stored #RRGGBB value into an RGB NumPy array."""
    if not value:
        return None
    text = value.strip().lstrip("#")
    if len(text) != 6:
        return None
    try:
        return np.array([int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)], dtype=float)
    except ValueError:
        return None


def colour_score(first: Optional[str], second: Optional[str]) -> float:
    """Return a simple 0-to-1 score for pairwise colour compatibility."""
    first_rgb = parse_hex_colour(first)
    second_rgb = parse_hex_colour(second)
    if first_rgb is None or second_rgb is None:
        return 0.5

    distance = float(np.linalg.norm(first_rgb - second_rgb))
    neutral = {"black", "white", "grey", "gray", "beige", "navy"}

    def is_neutral_hex(rgb: np.ndarray) -> bool:
        average = float(rgb.mean())
        spread = float(np.ptp(rgb))
        return spread < 35.0 and (average < 70.0 or average > 235.0)

    first_name = first.lower() if first else ""
    second_name = second.lower() if second else ""
    if first_name in neutral or second_name in neutral:
        return 0.9
    if is_neutral_hex(first_rgb) or is_neutral_hex(second_rgb):
        return 0.9

    base_score = 1.0 - min(distance / 441.67, 1.0)
    return float(max(0.0, base_score))


def category_score(first_category: str, second_category: str) -> float:
    """Return a simple compatibility score for two clothing categories."""
    first = first_category.strip().lower()
    second = second_category.strip().lower()
    if frozenset((first, second)) in COMPATIBLE_CATEGORY_PAIRS:
        return 1.0
    if first == second:
        return 0.2
    if {first, second}.issubset(UPPER_CATEGORIES | LOWER_CATEGORIES):
        return 0.7
    if second in SHOE_CATEGORIES or first in SHOE_CATEGORIES:
        return 0.8
    return 0.6


def get_embedding(item: Dict[str, Any]) -> np.ndarray:
    """Read an embedding from the database, or extract it from the image as a fallback."""
    raw = item.get("embedding_json")
    if raw:
        try:
            vector = np.asarray(json.loads(raw), dtype=float)
            if vector.size:
                return vector.reshape(-1)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    image_path = item.get("image_path")
    if image_path and Path(image_path).exists():
        with Image.open(image_path) as image:
            vector = extract_image_features(image)["embedding"]
            return np.asarray(vector, dtype=float).reshape(-1)

    return np.asarray([0.0], dtype=float)


def get_texture_vector(item: Dict[str, Any]) -> np.ndarray:
    """Read stored texture features as a small numeric vector."""
    raw = item.get("texture_features_json")
    if raw:
        try:
            texture = json.loads(raw)
            if isinstance(texture, dict):
                return np.asarray([
                    float(texture.get("mean_intensity", 0.0)),
                    float(texture.get("std_intensity", 0.0)),
                    float(texture.get("contrast", 0.0)),
                    float(texture.get("edge_density", 0.0)),
                ], dtype=float)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return np.zeros(4, dtype=float)


def cosine_similarity_score(first_vector: np.ndarray, second_vector: np.ndarray) -> float:
    """Convert cosine similarity to a 0-to-1 score, padding different lengths."""
    first = np.asarray(first_vector, dtype=float).reshape(-1)
    second = np.asarray(second_vector, dtype=float).reshape(-1)
    size = max(first.size, second.size)
    if size == 0:
        return 0.5

    first = np.pad(first, (0, size - first.size))
    second = np.pad(second, (0, size - second.size))
    if not np.any(first) or not np.any(second):
        return 0.5

    similarity = float(cosine_similarity(first.reshape(1, -1), second.reshape(1, -1))[0][0])
    return float(np.clip((similarity + 1.0) / 2.0, 0.0, 1.0))


def embedding_score(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    """Calculate cosine similarity between two clothing image embeddings."""
    return cosine_similarity_score(get_embedding(first), get_embedding(second))


def texture_similarity(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    """Compare extracted texture statistics using cosine similarity."""
    return cosine_similarity_score(get_texture_vector(first), get_texture_vector(second))


def item_category(item: Dict[str, Any]) -> str:
    return str(item.get("category", "")).strip().lower()


def is_complete(item: Dict[str, Any]) -> bool:
    return item_category(item) in COMPLETE_CATEGORIES


def is_upper(item: Dict[str, Any]) -> bool:
    return item_category(item) in UPPER_CATEGORIES


def is_lower(item: Dict[str, Any]) -> bool:
    return item_category(item) in LOWER_CATEGORIES


def is_shoe(item: Dict[str, Any]) -> bool:
    return item_category(item) in SHOE_CATEGORIES


def occasion_bonus(items: Iterable[Dict[str, Any]], occasion: Optional[str]) -> float:
    """Small score bonus when wardrobe item occasions match a requested occasion."""
    if not occasion:
        return 0.0
    selected = list(items)
    if not selected:
        return 0.0
    wanted = occasion.strip().lower()
    matches = sum(
        1 for item in selected
        if str(item.get("occasion", "")).strip().lower() in {wanted, "casual", "any", ""}
    )
    return min(matches / len(selected), 1.0) * 0.1


def weather_suitability_score(items: Iterable[Dict[str, Any]], occasion: Optional[str]) -> float:
    """Score based on how suitable the outfit is for the current weather."""
    if not occasion:
        return 0.0
    selected = list(items)
    if not selected:
        return 0.0
    season = get_season_for_weather(occasion)
    matches = sum(
        1 for item in selected
        if str(item.get("season", "")).strip().lower() == season
    )
    return min(matches / len(selected), 1.0) * 0.1


def weather_suitability(items: Iterable[Dict[str, Any]], weather: Optional[Dict[str, Any]] = None) -> float:
    """Score an outfit against temperature, season, rain, and item metadata."""
    selected = list(items)
    if not selected or not weather:
        return 0.5

    temperature = float(weather.get("temperature_c", 20.0))
    rain = bool(weather.get("rain", False))
    season = get_season_for_weather(weather)
    scores: List[float] = []

    for item in selected:
        score = 0.5
        item_season = str(item.get("season", "All-season")).strip().lower()
        category = item_category(item)
        fabric = str(item.get("fabric", "")).strip().lower()

        if item_season in {"all-season", "all season", ""}:
            score += 0.20
        elif item_season == season.lower():
            score += 0.25
        elif item_season in {"spring", "autumn"} and season in {"Spring", "Autumn"}:
            score += 0.10

        if temperature < 10:
            if category in {"jacket", "hoodie", "sweater", "coat", "boots"}:
                score += 0.20
            if category in {"shorts", "sandals", "skirt"}:
                score -= 0.30
            if fabric in {"wool", "denim", "leather"}:
                score += 0.10
        elif temperature < 18:
            if category in {"jacket", "hoodie", "sweater", "pants", "jeans", "boots"}:
                score += 0.10
            if category in {"shorts", "sandals"}:
                score -= 0.10
        elif temperature >= 27:
            if category in {"t-shirt", "shirt", "dress", "shorts", "skirt", "sandals"}:
                score += 0.12
            if category in {"jacket", "hoodie", "sweater", "boots"}:
                score -= 0.25
            if fabric in {"linen", "cotton"}:
                score += 0.08

        if rain:
            if category in {"boots", "jacket", "hoodie", "pants", "jeans"}:
                score += 0.12
            if category in {"sandals", "dress", "skirt"}:
                score -= 0.18

        scores.append(float(np.clip(score, 0.0, 1.0)))

    return float(np.clip(sum(scores) / len(scores), 0.0, 1.0))


def pair_score(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    """Combine embedding, texture, colour, and category scores for two items."""
    image_similarity = embedding_score(first, second)
    texture_compatibility = texture_similarity(first, second)
    colour_compatibility = colour_score(first.get("dominant_color"), second.get("dominant_color"))
    category_compatibility = category_score(item_category(first), item_category(second))
    return (
        (0.40 * image_similarity)
        + (0.15 * texture_compatibility)
        + (0.20 * colour_compatibility)
        + (0.25 * category_compatibility)
    )


def generate_outfit_combinations(
    wardrobe_items: List[Dict[str, Any]],
    occasion: Optional[str] = None,
    top_n: int = 5,
    weather: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate and rank suitable outfits using image, colour, and category signals."""
    available = [item for item in wardrobe_items if item.get("image_path") or item.get("id")]
    outfits: List[Dict[str, Any]] = []

    complete_items = [item for item in available if is_complete(item)]
    uppers = [item for item in available if is_upper(item)]
    lowers = [item for item in available if is_lower(item)]
    shoes = [item for item in available if is_shoe(item)]

    if uppers and lowers:
        for upper in uppers:
            for lower in lowers:
                selected = [upper, lower]

                base_pairs = list(combinations(selected, 2))
                base_score = sum(pair_score(first, second) for first, second in base_pairs) / len(base_pairs)
                base_score = hybrid_outfit_score(base_score, selected, occasion, weather)
                compatibility_probability = outfit_compatibility(selected)
                outfits.append({
                    "items": selected,
                    "score": round(float(base_score), 4),
                    "compatibility_probability": round(float(compatibility_probability), 4),
                    "weather_suitability": round(float(weather_suitability(selected, weather)), 4),
                    "item_ids": [int(item["id"]) for item in selected if item.get("id") is not None],
                    "reason": "Top and bottom compatibility",
                })

                for shoe in shoes:
                    outfit_items = selected + [shoe]
                    pairs = list(combinations(outfit_items, 2))
                    score = sum(pair_score(first, second) for first, second in pairs) / len(pairs)
                    score = hybrid_outfit_score(score, outfit_items, occasion, weather)
                    compatibility_probability = outfit_compatibility(outfit_items)
                    outfits.append({
                        "items": outfit_items,
                        "score": round(float(score), 4),
                        "compatibility_probability": round(float(compatibility_probability), 4),
                        "weather_suitability": round(float(weather_suitability(outfit_items, weather)), 4),
                        "item_ids": [int(item["id"]) for item in outfit_items if item.get("id") is not None],
                        "reason": "Top, bottom, and footwear compatibility",
                    })

    for complete in complete_items:
        outfit_items = [complete]
        rule_score = 0.5
        score = hybrid_outfit_score(rule_score, outfit_items, occasion, weather)
        compatibility_probability = outfit_compatibility(outfit_items)
        outfits.append({
            "items": outfit_items,
            "score": round(float(score), 4),
            "compatibility_probability": round(float(compatibility_probability), 4),
            "item_ids": [int(item["id"]) for item in outfit_items if item.get("id") is not None],
            "reason": "Complete one-piece outfit",
        })

        for shoe in shoes:
            outfit_items = [complete, shoe]
            rule_score = 0.5 + (0.5 * pair_score(complete, shoe))
            score = hybrid_outfit_score(rule_score, outfit_items, occasion, weather)
            compatibility_probability = outfit_compatibility(outfit_items)
            outfits.append({
                "items": outfit_items,
                "score": round(float(score), 4),
                "compatibility_probability": round(float(compatibility_probability), 4),
                "weather_suitability": round(float(weather_suitability(outfit_items, weather)), 4),
                "item_ids": [int(item["id"]) for item in outfit_items if item.get("id") is not None],
                "reason": "Complete outfit with matching footwear",
            })

    unique: Dict[tuple, Dict[str, Any]] = {}
    for outfit in outfits:
        if outfit["item_ids"]:
            key = tuple(sorted(outfit["item_ids"]))
        else:
            key = tuple(sorted((
                str(item.get("name", "")),
                str(item.get("category", "")),
                str(item.get("image_path", "")),
            ) for item in outfit["items"]))
        unique[key] = outfit

    ranked = sorted(unique.values(), key=lambda outfit: outfit["score"], reverse=True)
    return ranked[:max(int(top_n), 0)]


def calculate_similarity(first_item: Dict[str, Any], second_item: Dict[str, Any]) -> Dict[str, float]:
    """Expose the individual similarity scores used by the recommendation engine."""
    return {
        "embedding_similarity": round(embedding_score(first_item, second_item), 4),
        "texture_similarity": round(texture_similarity(first_item, second_item), 4),
        "colour_compatibility": round(colour_score(first_item.get("dominant_color"), second_item.get("dominant_color")), 4),
        "category_compatibility": round(category_score(item_category(first_item), item_category(second_item)), 4),
        "combined_score": round(pair_score(first_item, second_item), 4),
    }


def outfit_compatibility(items: Iterable[Dict[str, Any]]) -> float:
    """Get a 0-to-1 compatibility probability from the Milestone 6 model."""
    selected = list(items)
    if not selected:
        return 0.5
    try:
        return predict_compatibility(selected)
    except (OSError, ValueError, RuntimeError):
        # Keep Milestone 5 recommendations usable if model loading or inference fails.
        return 0.5


def hybrid_outfit_score(
    rule_score: float,
    items: Iterable[Dict[str, Any]],
    occasion: Optional[str] = None,
    weather: Optional[Dict[str, Any]] = None,
) -> float:
    """Blend rule, learned compatibility, occasion, and weather suitability scores."""
    selected = list(items)
    probability = outfit_compatibility(selected)

    if weather:
        weather_score = weather_suitability(selected, weather)
        result = (
            (0.65 * float(rule_score))
            + (0.20 * probability)
            + (0.15 * weather_score)
        )
    else:
        result = (0.75 * float(rule_score)) + (0.25 * probability)

    result += occasion_bonus(selected, occasion)
    return float(np.clip(result, 0.0, 1.0))

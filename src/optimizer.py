"""Integer-linear-programming outfit optimizer for Milestone 8."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import pulp

from src.compatibility_model import predict_compatibility
from src.recommendation import (
    UPPER_CATEGORIES,
    LOWER_CATEGORIES,
    SHOE_CATEGORIES,
    COMPLETE_CATEGORIES,
    item_category,
    occasion_bonus,
    pair_score,
    weather_suitability,
)


OUTERWEAR_CATEGORIES = {"jacket", "coat", "hoodie", "sweater"}
TOP_CATEGORIES = UPPER_CATEGORIES - OUTERWEAR_CATEGORIES


def is_valid_outfit(items: Sequence[Dict[str, Any]]) -> bool:
    """Verify the hard structure rules for a generated outfit."""
    categories = [item_category(item) for item in items if isinstance(item, dict)]
    shoes = sum(category in SHOE_CATEGORIES for category in categories)
    complete = sum(category in COMPLETE_CATEGORIES for category in categories)
    tops = sum(category in TOP_CATEGORIES for category in categories)
    lowers = sum(category in LOWER_CATEGORIES for category in categories)
    outerwear = sum(category in OUTERWEAR_CATEGORIES for category in categories)

    if shoes != 1:
        return False
    if outerwear > 1:
        return False

    if complete == 1:
        return tops == 0 and lowers == 0
    return tops == 1 and lowers == 1 and complete == 0


def preference_score(
    items: Iterable[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]] = None,
) -> float:
    """Score matching to simple user preferences, always in the 0-to-1 range."""
    selected = [item for item in items if isinstance(item, dict)]
    if not selected or not preferences:
        return 0.5

    fields = {
        "preferred_colours": "dominant_color",
        "preferred_fabrics": "fabric",
        "preferred_categories": "category",
        "preferred_seasons": "season",
        "preferred_occasions": "occasion",
    }
    scores: List[float] = []
    for preference_key, item_key in fields.items():
        wanted = preferences.get(preference_key, [])
        if not wanted:
            continue
        normalized = {str(value).strip().lower() for value in wanted}
        matches = sum(
            str(item.get(item_key, "")).strip().lower() in normalized
            for item in selected
        )
        scores.append(matches / len(selected))
    return float(min(max(sum(scores) / len(scores), 0.0), 1.0)) if scores else 0.5


def _item_key(item: Dict[str, Any]) -> str:
    item_id = item.get("id")
    return str(item_id) if item_id is not None else "{}|{}|{}".format(
        item.get("name", ""), item.get("category", ""), item.get("image_path", "")
    )


def _style_score(items: Sequence[Dict[str, Any]]) -> float:
    pair_scores = [pair_score(first, second) for first, second in combinations(items, 2)]
    rule_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.5
    try:
        learned_score = predict_compatibility(items)
    except (OSError, ValueError, RuntimeError):
        learned_score = 0.5
    return float((0.65 * rule_score) + (0.35 * learned_score))


def _build_candidates(
    wardrobe_items: Sequence[Dict[str, Any]],
    occasion: Optional[str],
    weather: Optional[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]],
    recently_worn_ids: Iterable[Any],
) -> List[Dict[str, Any]]:
    available = [item for item in wardrobe_items if item.get("image_path") or item.get("id")]
    tops = [item for item in available if item_category(item) in TOP_CATEGORIES]
    lowers = [item for item in available if item_category(item) in LOWER_CATEGORIES]
    shoes = [item for item in available if item_category(item) in SHOE_CATEGORIES]
    complete = [item for item in available if item_category(item) in COMPLETE_CATEGORIES]
    outerwear = [item for item in available if item_category(item) in OUTERWEAR_CATEGORIES]

    recently = {str(value) for value in recently_worn_ids}
    candidates: List[Dict[str, Any]] = []

    def add_candidate(items: Sequence[Dict[str, Any]], reason: str) -> None:
        if not is_valid_outfit(items):
            return
        selected_keys = {_item_key(item) for item in items}
        recent_matches = sum(key in recently for key in selected_keys)
        repetition_penalty = recent_matches / max(len(selected_keys), 1)

        exact_keys = tuple(sorted(selected_keys))
        weather_score = weather_suitability(items, weather)
        occasion_score = occasion_bonus(items, occasion)
        preference = preference_score(items, preferences)
        style = _style_score(items)
        candidates.append({
            "items": list(items),
            "item_ids": [int(item["id"]) for item in items if item.get("id") is not None],
            "exact_keys": exact_keys,
            "style_score": style,
            "weather_score": weather_score,
            "occasion_score": occasion_score,
            "preference_score": preference,
            "repetition_penalty": repetition_penalty,
            "reason": reason,
        })

    for top in tops:
        for lower in lowers:
            for shoe in shoes:
                add_candidate([top, lower, shoe], "Top, bottom, and footwear")
                for layer in outerwear:
                    add_candidate([top, lower, shoe, layer], "Top, bottom, footwear, and outerwear")

    for dress in complete:
        for shoe in shoes:
            add_candidate([dress, shoe], "Dress and footwear")
            for layer in outerwear:
                add_candidate([dress, shoe, layer], "Dress, footwear, and outerwear")

    unique: Dict[tuple, Dict[str, Any]] = {}
    for candidate in candidates:
        unique[candidate["exact_keys"]] = candidate
    return list(unique.values())


def optimize_outfits(
    wardrobe_items: Sequence[Dict[str, Any]],
    occasion: Optional[str] = None,
    weather: Optional[Dict[str, Any]] = None,
    preferences: Optional[Dict[str, Any]] = None,
    recently_worn_ids: Optional[Iterable[Any]] = None,
    top_n: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Use binary ILP candidate variables to generate different valid top outfits.

    The objective is style + weather + occasion + preference - repetition.
    Hard constraints are encoded only in the candidate set; invalid structures
    are never passed to PuLP as possible outfits.
    """
    limit = max(0, int(top_n))
    if limit == 0:
        return []

    candidates = _build_candidates(
        wardrobe_items,
        occasion,
        weather,
        preferences,
        recently_worn_ids or [],
    )
    if not candidates:
        return []

    selected: Set[tuple] = set()
    results: List[Dict[str, Any]] = []
    default_weights = {
        "style": 1.0,
        "weather": 1.0,
        "occasion": 1.0,
        "preference": 1.0,
        "repetition": 1.0,
    }
    weight_values = default_weights.copy()
    if weights:
        weight_values.update(weights)

    for _ in range(limit):
        problem = pulp.LpProblem("outfit_optimization", pulp.LpMaximize)
        variables = {
            candidate["exact_keys"]: pulp.LpVariable(
                "outfit_{}".format(index), cat="Binary"
            )
            for index, candidate in enumerate(candidates)
        }

        problem += pulp.lpSum(variables.values()) == 1

        for excluded in selected:
            if excluded in variables:
                problem += variables[excluded] == 0

        objective_terms = []
        for candidate in candidates:
            variable = variables[candidate["exact_keys"]]
            score = (
                weight_values["style"] * candidate["style_score"]
                + weight_values["weather"] * candidate["weather_score"]
                + weight_values["occasion"] * candidate["occasion_score"]
                + weight_values["preference"] * candidate["preference_score"]
                - weight_values["repetition"] * candidate["repetition_penalty"]
            )
            objective_terms.append(score * variable)
        problem += pulp.lpSum(objective_terms)

        solver = pulp.PULP_CBC_CMD(msg=False)
        status = problem.solve(solver)
        if pulp.LpStatus[status] != "Optimal":
            break

        chosen = next(
            candidate for candidate in candidates
            if pulp.value(variables[candidate["exact_keys"]]) == 1
        )
        score = (
            weight_values["style"] * chosen["style_score"]
            + weight_values["weather"] * chosen["weather_score"]
            + weight_values["occasion"] * chosen["occasion_score"]
            + weight_values["preference"] * chosen["preference_score"]
            - weight_values["repetition"] * chosen["repetition_penalty"]
        )
        output = {
            "items": chosen["items"],
            "item_ids": chosen["item_ids"],
            "score": round(float(score), 4),
            "compatibility_probability": round(float(chosen["style_score"]), 4),
            "weather_suitability": round(float(chosen["weather_score"]), 4),
            "occasion_suitability": round(float(chosen["occasion_score"]), 4),
            "preference_score": round(float(chosen["preference_score"]), 4),
            "repetition_penalty": round(float(chosen["repetition_penalty"]), 4),
            "reason": chosen["reason"],
        }
        results.append(output)
        selected.add(chosen["exact_keys"])

    return results

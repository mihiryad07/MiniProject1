"""Offline ranking and compatibility-model evaluation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np


def precision_at_k(relevant_ids: Iterable[str], ranked_ids: Sequence[str], k: int) -> float:
    """Return Precision@K for one ranking."""
    relevant = set(str(item) for item in relevant_ids)
    ranked = [str(item) for item in ranked_ids[:max(k, 0)]]
    if not ranked:
        return 0.0
    return sum(item in relevant for item in ranked) / len(ranked)


def recall_at_k(relevant_ids: Iterable[str], ranked_ids: Sequence[str], k: int) -> float:
    """Return Recall@K for one ranking."""
    relevant = set(str(item) for item in relevant_ids)
    ranked = [str(item) for item in ranked_ids[:max(k, 0)]]
    if not relevant:
        return 0.0
    return sum(item in relevant for item in ranked) / len(relevant)


def average_precision(relevant_ids: Iterable[str], ranked_ids: Sequence[str]) -> float:
    """Calculate average precision for one complete ranking."""
    relevant = set(str(item) for item in relevant_ids)
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for rank, item_id in enumerate(ranked_ids, start=1):
        if str(item_id) in relevant:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / len(relevant)


def mean_average_precision(relevant_rankings: Mapping[str, Iterable[str]], all_rankings: Mapping[str, Sequence[str]]) -> float:
    """Calculate MAP across users or queries."""
    if not relevant_rankings:
        return 0.0
    values = [
        average_precision(relevant_ids, all_rankings.get(query_id, []))
        for query_id, relevant_ids in relevant_rankings.items()
    ]
    return float(np.mean(values))

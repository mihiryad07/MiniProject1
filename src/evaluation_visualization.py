"""Generate evaluation plots for college-submission documentation."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

import matplotlib.pyplot as plt


def plot_classifier_metrics(metrics: Mapping[str, float], output_path: Optional[Path] = None) -> Path:
    """Plot recorded compatibility-model classification metrics."""
    names = ["accuracy", "precision", "recall", "f1_score"]
    values = [float(metrics.get(name, 0.0) or 0.0) for name in names]

    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar([name.replace("_", " ").title() for name in names], values, color="#7259D9")
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Score")
    axis.set_title("Compatibility Classifier Evaluation")
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{value:.3f}", ha="center")

    destination = Path(output_path or "assets/evaluation/model_metrics.png")
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)
    return destination

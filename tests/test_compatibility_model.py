import numpy as np

from src.compatibility_model import (
    extract_combination_features,
    generate_negative_examples,
    prepare_training_data,
    predict_compatibility,
    train_model,
)


def test_extract_combination_features_has_fixed_shape():
    items = [
        {"category": "shirt", "dominant_color": "#FFFFFF", "occasion": "Casual"},
        {"category": "jeans", "dominant_color": "#336699", "occasion": "Casual"},
    ]

    features = extract_combination_features(items)

    assert isinstance(features, np.ndarray)
    assert features.dtype == np.float64
    assert features.shape[0] >= 35


def test_negative_examples_are_generated_for_positive_examples():
    positive = [
        [{"category": "shirt", "dominant_color": "#FFFFFF"},
         {"category": "jeans", "dominant_color": "#336699"}],
    ]

    negatives = generate_negative_examples(positive)

    assert len(negatives) > 0


def test_fallback_training_is_real_and_reported(tmp_path):
    model_path = tmp_path / "compatibility.joblib"
    result = train_model(model_path=model_path)

    assert model_path.exists()
    assert result["metadata"]["dataset_name"] == "Fallback sample data"
    assert 0.0 <= result["metrics"]["accuracy"] <= 1.0
    assert 0.0 <= result["metrics"]["precision"] <= 1.0
    assert 0.0 <= result["metrics"]["recall"] <= 1.0
    assert 0.0 <= result["metrics"]["f1_score"] <= 1.0


def test_compatibility_probability_is_between_zero_and_one(tmp_path):
    model_path = tmp_path / "compatibility.joblib"
    train_model(model_path=model_path)
    items = [
        {"category": "shirt", "dominant_color": "#FFFFFF", "fabric": "cotton", "season": "all"},
        {"category": "jeans", "dominant_color": "#336699", "fabric": "cotton", "season": "all"},
    ]

    probability = predict_compatibility(items, model_path=model_path)

    assert 0.0 <= probability <= 1.0

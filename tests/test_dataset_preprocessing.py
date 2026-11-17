from pathlib import Path

import pandas as pd

from src.data.preprocessing import clean_dataset, normalize_categorical_columns, split_dataframe


def test_clean_dataset_removes_duplicates_and_fills_missing():
    df = pd.DataFrame(
        {
            "category": ["shirt", "shirt", None],
            "color": ["red", "red", "blue"],
            "occasion": ["casual", "casual", "formal"],
            "price": [100.0, 100.0, None],
        }
    )

    cleaned = clean_dataset(df)

    assert cleaned.shape[0] == 2
    assert cleaned["category"].isna().sum() == 0
    assert cleaned["price"].isna().sum() == 0


def test_normalize_categorical_columns_lowercases_values():
    df = pd.DataFrame({"category": [" Shirt ", "PANTS"], "color": [" Red ", "Blue"]})
    cleaned = normalize_categorical_columns(df, ["category", "color"])

    assert cleaned["category"].tolist() == ["shirt", "pants"]
    assert cleaned["color"].tolist() == ["red", "blue"]


def test_split_dataframe_returns_train_and_test_sets():
    df = pd.DataFrame(
        {
            "category": ["shirt", "pants", "dress", "jacket", "hoodie", "sweater"],
            "color": ["red", "blue", "green", "black", "white", "gray"],
            "target": [0, 1, 0, 1, 0, 1],
        }
    )

    X_train, X_test, y_train, y_test = split_dataframe(df, target_column="target", test_size=0.33, random_state=42)

    assert len(X_train) == 4
    assert len(X_test) == 2
    assert len(y_train) == 4
    assert len(y_test) == 2
    assert set(y_train.unique()).issubset({0, 1})

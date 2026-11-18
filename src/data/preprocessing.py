from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.model_selection import train_test_split


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a clothing dataset by handling missing values and duplicates."""
    cleaned_df = df.copy()

    cleaned_df = cleaned_df.drop_duplicates()

    for column in cleaned_df.columns:
        if is_numeric_dtype(cleaned_df[column]):
            cleaned_df[column] = cleaned_df[column].fillna(cleaned_df[column].median())
        else:
            cleaned_df[column] = cleaned_df[column].fillna("unknown")

    return cleaned_df.reset_index(drop=True)


def normalize_categorical_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Normalize categorical values to lowercase strings and trim spaces."""
    result = df.copy()

    for column in columns:
        if column in result.columns:
            result[column] = result[column].astype(str).str.strip().str.lower()

    return result


def organize_image_metadata(df: pd.DataFrame, image_column: str, metadata_columns: Iterable[str]) -> pd.DataFrame:
    """Organize image path and metadata columns into a consistent layout."""
    result = df.copy()

    if image_column not in result.columns:
        raise ValueError(f"Image column '{image_column}' not found in dataset.")

    for column in metadata_columns:
        if column not in result.columns:
            continue
        result[column] = result[column].fillna("unknown")

    result[image_column] = result[image_column].astype(str).str.strip()
    return result


def split_dataframe(
    df: pd.DataFrame,
    target_column: str,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split the dataset into train and test sets.

    Returns:
        X_train, X_test, y_train, y_test
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    X = df.drop(columns=[target_column])
    y = df[target_column]

    stratify_param = y if stratify else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_param,
    )

    return X_train, X_test, y_train, y_test


def generate_dataset_report(df: pd.DataFrame, output_dir: str | os.PathLike | None = None) -> Dict[str, str]:
    """Create a simple dataset summary report without requiring plotting packages."""
    output_path = Path(output_dir) if output_dir is not None else Path("data/processed")
    output_path.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "Dataset Summary Report",
        "======================",
        f"Rows: {len(df)}",
        f"Columns: {len(df.columns)}",
        "",
        "Column names:",
    ]

    for column in df.columns:
        report_lines.append(f"- {column}")

    if "category" in df.columns:
        report_lines.append("")
        report_lines.append("Category counts:")
        for category, count in df["category"].value_counts().items():
            report_lines.append(f"- {category}: {count}")

    if "color" in df.columns:
        report_lines.append("")
        report_lines.append("Top colors:")
        for color, count in df["color"].value_counts().head(10).items():
            report_lines.append(f"- {color}: {count}")

    report_file = output_path / "dataset_summary_report.txt"
    report_file.write_text("\n".join(report_lines), encoding="utf-8")

    return {"dataset_summary": str(report_file)}


def prepare_clothing_dataset(
    file_path: str | os.PathLike,
    target_column: str,
    categorical_columns: Iterable[str] | None = None,
    image_column: str = "image_path",
    metadata_columns: Iterable[str] | None = None,
    output_dir: str | os.PathLike | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, Dict[str, str]]:
    """Load, clean, and prepare a clothing dataset for later machine learning tasks."""
    df = pd.read_csv(file_path) if str(file_path).lower().endswith(".csv") else pd.read_json(file_path)

    if categorical_columns is None:
        categorical_columns = ["category", "color", "occasion", "texture", "style"]
    if metadata_columns is None:
        metadata_columns = ["image_path", "image_name", "source"]

    df = clean_dataset(df)
    df = normalize_categorical_columns(df, categorical_columns)
    df = organize_image_metadata(df, image_column=image_column, metadata_columns=metadata_columns)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found after cleaning.")

    X_train, X_test, y_train, y_test = split_dataframe(df, target_column=target_column, test_size=0.2)
    plots = generate_dataset_report(df, output_dir=output_dir)

    return df, X_train, X_test, y_train, y_test, plots

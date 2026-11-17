from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pandas as pd

from src.config import BASE_DIR


def find_dataset_files(data_dir: Optional[str | os.PathLike] = None) -> List[Path]:
    """Return all supported dataset files inside a directory.

    Supported formats: CSV, Excel, JSON, and Parquet.
    """
    target_dir = Path(data_dir) if data_dir is not None else BASE_DIR / "data"

    if not target_dir.exists():
        return []

    extensions = (".csv", ".xlsx", ".xls", ".json", ".parquet")
    files = [
        path for path in target_dir.rglob("*") if path.is_file() and path.suffix.lower() in extensions
    ]
    return sorted(files)


def load_dataset(file_path: str | os.PathLike) -> pd.DataFrame:
    """Load a dataset from CSV, Excel, JSON or Parquet file.

    Args:
        file_path: dataset file path.

    Returns:
        DataFrame with the dataset content.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)

    raise ValueError(f"Unsupported dataset format: {suffix}. Use CSV, Excel, JSON, or Parquet.")


def print_dataset_summary(df: pd.DataFrame) -> None:
    """Print a beginner-friendly summary of the dataset structure."""
    print("Dataset shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())

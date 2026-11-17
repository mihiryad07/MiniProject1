# Data preprocessing module

This folder contains the dataset loading and cleaning utilities for the wardrobe recommendation project.

## Purpose

- load data files
- inspect raw columns and structure
- clean invalid values
- remove duplicates
- prepare categorical variables
- split data into train/test sets
- generate a simple dataset summary report

## Typical usage

```python
from src.data.preprocessing import prepare_clothing_dataset

clean_df, x_train, x_test, y_train, y_test, report = prepare_clothing_dataset(
    file_path="data/raw/clothing_dataset.csv",
    target_column="label",
    categorical_columns=["category", "color", "occasion", "texture"],
    image_column="image_path",
    metadata_columns=["image_path", "image_name", "source"],
    output_dir="data/processed",
)
```

## Notes

This module is intentionally beginner-friendly and designed to work with simple CSV-based fashion data.

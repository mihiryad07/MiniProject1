"""Wardrobe operations that connect image processing with SQLite storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union
import json

from PIL import Image

from src.config import DATABASE_PATH
from src.database import (
    add_wardrobe_item,
    delete_wardrobe_item,
    get_or_create_default_user,
    get_wardrobe_item,
    get_wardrobe_items,
    initialize_database,
    update_wardrobe_item,
)
from src.feature_extraction import extract_image_features
from src.image_processing import process_uploaded_image


def rgb_to_hex(rgb: Dict[str, int]) -> str:
    """Convert an extracted RGB dictionary to a CSS-style hex colour."""
    return "#{:02X}{:02X}{:02X}".format(rgb["r"], rgb["g"], rgb["b"])


def add_clothing_item(
    uploaded_file: Any,
    name: str,
    category: str,
    fabric: str,
    season: str,
    occasion: str,
    db_path: Union[str, Path] = DATABASE_PATH,
) -> Dict[str, Any]:
    """Process an upload, extract its dominant colour, and save it to SQLite."""
    initialize_database(db_path)

    processed = process_uploaded_image(
        uploaded_file,
        output_dir=Path(db_path).parent / "processed",
        remove_bg=False,
    )

    with Image.open(processed["saved_path"]) as pil_image:
        features = extract_image_features(pil_image)

    user_id = get_or_create_default_user(db_path)
    item_id = add_wardrobe_item(
        db_path,
        {
            "user_id": user_id,
            "name": name.strip(),
            "category": category.strip(),
            "image_path": processed["saved_path"],
            "dominant_color": rgb_to_hex(features["dominant_color"]),
            "fabric": fabric.strip(),
            "season": season.strip(),
            "occasion": occasion.strip(),
            "embedding_json": json.dumps(features["embedding"]),
            "texture_features_json": json.dumps(features["texture_features"]),
        },
    )

    item = get_wardrobe_item(db_path, item_id)
    if item is None:
        raise RuntimeError("The clothing item could not be loaded after insertion.")
    return item


def list_clothing_items(db_path: Union[str, Path] = DATABASE_PATH) -> list[Dict[str, Any]]:
    """Return all clothing items for the local wardrobe user."""
    initialize_database(db_path)
    user_id = get_or_create_default_user(db_path)
    return get_wardrobe_items(db_path, user_id)


def get_clothing_item(item_id: int, db_path: Union[str, Path] = DATABASE_PATH) -> Optional[Dict[str, Any]]:
    """Return a wardrobe item by id."""
    initialize_database(db_path)
    return get_wardrobe_item(db_path, item_id)


def update_clothing_item(item_id: int, changes: Dict[str, Any], db_path: Union[str, Path] = DATABASE_PATH) -> bool:
    """Update editable clothing information."""
    initialize_database(db_path)
    return update_wardrobe_item(db_path, item_id, changes)


def delete_clothing_item(item_id: int, db_path: Union[str, Path] = DATABASE_PATH) -> bool:
    """Delete a clothing item and leave image deletion as an optional UI policy."""
    initialize_database(db_path)
    return delete_wardrobe_item(db_path, item_id)

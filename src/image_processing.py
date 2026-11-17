from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageOps

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_TARGET_SIZE = (224, 224)


def validate_image_file(file: Union[str, os.PathLike, Any]) -> bool:
    """Check whether the uploaded file exists and has a supported image extension."""
    if file is None:
        return False

    if isinstance(file, (str, os.PathLike)):
        path = Path(file)
        if not path.exists():
            return False
        return path.suffix.lower() in ALLOWED_EXTENSIONS

    filename = getattr(file, "name", None)
    if filename is None:
        return False

    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def resize_image(image: Union[Image.Image, np.ndarray], target_size: Tuple[int, int] = DEFAULT_TARGET_SIZE) -> Image.Image:
    """Resize an image to a standard size using PIL."""
    pil_image = image if isinstance(image, Image.Image) else Image.fromarray(np.array(image).astype(np.uint8))
    return pil_image.resize(target_size, Image.Resampling.LANCZOS)


def remove_background(image: Union[Image.Image, np.ndarray]) -> Image.Image:
    """Attempt to remove the background using a simple foreground segmentation approach.

    This is a lightweight method suitable for beginner projects and works best on clear clothing images.
    """
    pil_image = image if isinstance(image, Image.Image) else Image.fromarray(np.array(image).astype(np.uint8))
    rgb = ImageOps.exif_transpose(pil_image).convert("RGBA")
    data = np.array(rgb)

    mask = np.zeros(data.shape[:2], dtype=np.uint8)
    lower = np.array([60, 60, 60, 0], dtype=np.uint8)
    upper = np.array([255, 255, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(data, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    alpha = np.where(mask > 0, 255, 0).astype(np.uint8)
    rgba = np.dstack([data[:, :, :3], alpha])
    return Image.fromarray(rgba, mode="RGBA")


def preprocess_image(
    image: Union[Image.Image, np.ndarray],
    target_size: Tuple[int, int] = DEFAULT_TARGET_SIZE,
    remove_bg: bool = True,
) -> Image.Image:
    """Apply a standard preprocessing pipeline to a clothing image."""
    pil_image = image if isinstance(image, Image.Image) else Image.fromarray(np.array(image).astype(np.uint8))
    pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")

    if remove_bg:
        pil_image = remove_background(pil_image)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

    return resize_image(pil_image, target_size=target_size)


def save_processed_image(image: Image.Image, output_path: Union[str, os.PathLike]) -> str:
    """Save the processed image to disk and return the saved path."""
    file_path = Path(output_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(file_path)
    return str(file_path)


def process_uploaded_image(
    uploaded_file: Any,
    output_dir: Union[str, os.PathLike] = "data/processed",
    target_size: Tuple[int, int] = DEFAULT_TARGET_SIZE,
    remove_bg: bool = True,
) -> Dict[str, Any]:
    """Process an uploaded clothing image and return metadata and the saved output path."""
    if uploaded_file is None:
        raise ValueError("No image uploaded.")

    if not validate_image_file(uploaded_file):
        raise ValueError("Unsupported file type. Use PNG, JPG, JPEG, or WEBP.")

    image = Image.open(uploaded_file)
    processed = preprocess_image(image, target_size=target_size, remove_bg=remove_bg)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved_path = output_path / f"processed_{uploaded_file.name}"
    processed.save(saved_path)

    return {
        "original_name": uploaded_file.name,
        "saved_path": str(saved_path),
        "width": processed.width,
        "height": processed.height,
        "mode": processed.mode,
    }

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

import cv2
import numpy as np
from PIL import Image


def to_rgb_image(image: Union[Image.Image, np.ndarray, Any]) -> Image.Image:
    """Convert an image-like object to a PIL Image in RGB format."""
    if isinstance(image, Image.Image):
        return image.convert("RGB")

    if isinstance(image, np.ndarray):
        return Image.fromarray(image.astype(np.uint8)).convert("RGB")

    raise TypeError("Unsupported image type. Use a PIL image or NumPy array.")


def extract_dominant_color(image: Union[Image.Image, np.ndarray]) -> Dict[str, int]:
    """Return the most common color in the image using a simple quantized histogram."""
    rgb_image = np.array(to_rgb_image(image), dtype=np.uint8)
    resized = cv2.resize(rgb_image, (64, 64), interpolation=cv2.INTER_AREA)
    flat = resized.reshape(-1, 3)

    quantized = flat // 32
    combined = quantized[:, 0] * 64 + quantized[:, 1] * 8 + quantized[:, 2]
    unique_values, counts = np.unique(combined, return_counts=True)
    dominant_index = int(unique_values[np.argmax(counts)])

    r = int((dominant_index // 64) * 32)
    g = int(((dominant_index % 64) // 8) * 32)
    b = int((dominant_index % 8) * 32)

    return {"r": r, "g": g, "b": b}


def extract_texture_features(image: Union[Image.Image, np.ndarray]) -> Dict[str, float]:
    """Return simple texture statistics based on grayscale intensity and edge density."""
    rgb_image = np.array(to_rgb_image(image), dtype=np.uint8)
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    edges = cv2.Canny(gray, 50, 150)

    texture_features = {
        "mean_intensity": float(gray.mean()),
        "std_intensity": float(gray.std()),
        "contrast": float(laplacian.var()),
        "edge_density": float(np.mean(edges > 0)),
    }

    return texture_features


def generate_image_embedding(image: Union[Image.Image, np.ndarray], target_size: Tuple[int, int] = (224, 224)) -> List[float]:
    """Generate an embedding vector for the image.

    If TensorFlow/Keras with MobileNetV2 is available, a real MobileNetV2 embedding is used.
    Otherwise, a lightweight fallback vector is produced so the system remains functional.
    """
    rgb_image = np.array(to_rgb_image(image), dtype=np.float32)
    resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_AREA)

    try:
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

        model = MobileNetV2(weights="imagenet", include_top=False, pooling="avg")
        processed = preprocess_input(resized)
        embedding = model.predict(np.expand_dims(processed, axis=0), verbose=0)
        return embedding.reshape(-1).astype(float).tolist()
    except Exception:
        fallback = cv2.resize(rgb_image, (32, 32), interpolation=cv2.INTER_AREA) / 255.0
        return fallback.reshape(-1).astype(float).tolist()


def extract_image_features(image: Union[Image.Image, np.ndarray]) -> Dict[str, Any]:
    """Return all extracted image features in one structured dictionary."""
    rgb_image = to_rgb_image(image)

    return {
        "dominant_color": extract_dominant_color(rgb_image),
        "texture_features": extract_texture_features(rgb_image),
        "embedding": generate_image_embedding(rgb_image),
        "width": rgb_image.width,
        "height": rgb_image.height,
    }

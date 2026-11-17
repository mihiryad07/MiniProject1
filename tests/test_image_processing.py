from pathlib import Path

import numpy as np
from PIL import Image

from src.image_processing import preprocess_image, process_uploaded_image, validate_image_file


def test_validate_image_file_accepts_supported_extensions(tmp_path):
    file_path = tmp_path / "shirt.png"
    file_path.write_bytes(b"fake png data")

    assert validate_image_file(file_path) is True


def test_preprocess_image_returns_expected_size():
    image = Image.new("RGB", (800, 600), color="blue")
    processed = preprocess_image(image, target_size=(224, 224), remove_bg=False)

    assert processed.size == (224, 224)


def test_process_uploaded_image_saves_output(tmp_path):
    image = Image.new("RGB", (100, 100), color="green")
    file_path = tmp_path / "sample.jpg"
    image.save(file_path)

    result = process_uploaded_image(type("UploadedFile", (), {"name": "sample.jpg", "read": lambda self: file_path.read_bytes()})(), output_dir=tmp_path / "output", remove_bg=False)

    assert result["width"] == 224
    assert result["height"] == 224
    assert Path(result["saved_path"]).exists()

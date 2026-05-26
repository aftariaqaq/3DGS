from __future__ import annotations

from pathlib import Path

from PIL import Image

from packages.frame_select.scoring import GrayImage


def load_grayscale_image(path: Path, *, max_size: int = 64) -> GrayImage:
    with Image.open(path) as image:
        gray = image.convert("L")
        gray.thumbnail((max_size, max_size))
        width, height = gray.size
        pixels = list(gray.tobytes())
    return [pixels[row * width : (row + 1) * width] for row in range(height)]

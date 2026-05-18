"""Document rendering helpers for CV-vs-Non-CV classification."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import fitz
import numpy as np
from PIL import Image, ImageOps


SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def is_supported_document(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def supported_files(root: str | Path) -> Iterable[Path]:
    root_path = Path(root)
    for path in root_path.rglob("*"):
        if path.is_file() and is_supported_document(path):
            yield path


def render_document_page(path: str | Path, *, dpi: int = 144) -> Image.Image:
    """Render the first page/frame of a PDF or image document as grayscale PIL image."""
    document_path = Path(path)
    suffix = document_path.suffix.lower()

    if suffix == ".pdf":
        with fitz.open(document_path) as pdf:
            if pdf.page_count == 0:
                raise ValueError(f"PDF has no pages: {document_path}")
            page = pdf.load_page(0)
            zoom = dpi / 72
            pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    else:
        with Image.open(document_path) as image_file:
            image_file.seek(0)
            image = image_file.convert("RGB")

    return ImageOps.grayscale(image)


def resize_with_padding(image: Image.Image, image_size: tuple[int, int]) -> Image.Image:
    """Resize while preserving page aspect ratio, then pad to fixed model size."""
    height, width = image_size
    contained = ImageOps.contain(image, (width, height), Image.Resampling.BILINEAR)
    canvas = Image.new("L", (width, height), color=255)
    left = (width - contained.width) // 2
    top = (height - contained.height) // 2
    canvas.paste(contained, (left, top))
    return canvas


def document_to_array(path: str | Path, *, image_size: tuple[int, int] = (160, 224), dpi: int = 144) -> np.ndarray:
    """Return a fixed-size uint8 grayscale page image array."""
    image = render_document_page(path, dpi=dpi)
    image = resize_with_padding(image, image_size)
    return np.asarray(image, dtype=np.uint8)


def array_to_tensor(array: np.ndarray):
    """Convert uint8 grayscale page image to normalized torch tensor without importing torch globally."""
    import torch

    normalized = array.astype("float32") / 255.0
    normalized = (normalized - 0.5) / 0.5
    return torch.from_numpy(normalized).unsqueeze(0)

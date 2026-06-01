from __future__ import annotations

import os
import re
import shutil
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageFilter, ImageOps


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


class OCRConfigurationError(RuntimeError):
    pass


class OCRServiceError(RuntimeError):
    pass


@dataclass
class OCRResult:
    text: str
    metadata: dict


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, min_value: int, max_value: int) -> int:
    raw = _env(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, min(max_value, value))


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _ensure_tesseract_available() -> None:
    cmd = _env("OCR_TESSERACT_CMD", "").strip()
    if cmd:
        return

    if shutil.which("tesseract"):
        return

    raise OCRConfigurationError(
        "Tesseract is not installed or not available in PATH. "
        "On macOS run: brew install tesseract tesseract-lang. "
        "If it is installed in a custom path, set OCR_TESSERACT_CMD in .env."
    )


def _render_pdf_pages(pdf_bytes: bytes) -> tuple[list[Image.Image], dict]:
    try:
        import fitz  # PyMuPDF
    except Exception as exc:
        raise OCRConfigurationError(
            "PyMuPDF is required for PDF rendering. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    dpi = _int_env("OCR_DPI", default=220, min_value=120, max_value=320)
    max_pages = _int_env("OCR_MAX_PDF_PAGES", default=50, min_value=1, max_value=500)

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise OCRServiceError(f"Could not open PDF for OCR: {exc}") from exc

    page_count = len(document)
    if page_count == 0:
        raise OCRServiceError("The PDF has no pages.")

    if page_count > max_pages:
        raise OCRServiceError(
            f"This PDF has {page_count} pages, but OCR_MAX_PDF_PAGES is {max_pages}. "
            "Increase OCR_MAX_PDF_PAGES in .env if you want to process larger PDFs."
        )

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    images: list[Image.Image] = []
    for page in document:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(image)

    return images, {
        "page_count": page_count,
        "dpi": dpi,
        "max_pages": max_pages,
    }


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    if not _bool_env("OCR_PREPROCESS", True):
        return image

    # Simple, safe preprocessing:
    # - grayscale improves OCR consistency
    # - autocontrast improves faint scanned pages
    # - median filter reduces minor noise
    img = image.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


def _ocr_page(image: Image.Image, page_number: int) -> str:
    _ensure_tesseract_available()

    try:
        import pytesseract
    except Exception as exc:
        raise OCRConfigurationError(
            "pytesseract is required. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    cmd = _env("OCR_TESSERACT_CMD", "").strip()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    languages = _env("OCR_LANGUAGES", "ara+eng")
    config = _env("OCR_TESSERACT_CONFIG", "--oem 3 --psm 6 -c preserve_interword_spaces=1")

    image = _preprocess_for_ocr(image)

    try:
        text = pytesseract.image_to_string(image, lang=languages, config=config)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRConfigurationError(
            "Tesseract executable was not found. On macOS run: brew install tesseract tesseract-lang."
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OCRServiceError(
            f"Tesseract OCR failed on page {page_number}. "
            f"Check that languages are installed using: tesseract --list-langs. Error: {exc}"
        ) from exc

    return _clean_text(text)


def ocr_pdf_locally(pdf_bytes: bytes, filename: str = "document.pdf") -> OCRResult:
    provider = _env("OCR_PROVIDER", "local_tesseract").strip().lower()
    if provider != "local_tesseract":
        raise OCRConfigurationError(
            f"Unsupported OCR_PROVIDER={provider!r}. Use OCR_PROVIDER=local_tesseract for the free local OCR mode."
        )

    pages, render_meta = _render_pdf_pages(pdf_bytes)

    chunks: list[str] = []
    empty_pages: list[int] = []

    for index, image in enumerate(pages, start=1):
        page_text = _ocr_page(image, index)
        if page_text:
            chunks.append(f"## Page {index}\n{page_text}")
        else:
            empty_pages.append(index)

        # Very small pause to keep CPU usage smoother.
        time.sleep(0.02)

    text = _clean_text("\n\n".join(chunks))
    if not text:
        raise OCRServiceError("OCR completed, but no readable text was extracted from the PDF.")

    return OCRResult(
        text=text,
        metadata={
            "filename": filename,
            "type": "pdf",
            "provider": "local_tesseract",
            "ocr_forced": True,
            "ocr_needed": False,
            "languages": _env("OCR_LANGUAGES", "ara+eng"),
            "tesseract_config": _env("OCR_TESSERACT_CONFIG", "--oem 3 --psm 6 -c preserve_interword_spaces=1"),
            "empty_pages": empty_pages,
            **render_meta,
        },
    )

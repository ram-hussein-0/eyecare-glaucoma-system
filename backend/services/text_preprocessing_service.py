from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


ARABIC_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

TATWEEL_RE = re.compile(r"\u0640+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
DASH_LINE_RE = re.compile(r"^\s*[-_=ـ]{4,}\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*(page\s*)?\d{1,4}\s*$", re.IGNORECASE)


@dataclass
class ProcessedText:
    text: str
    metadata: dict


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _int_env(name: str, default: int, min_value: int, max_value: int) -> int:
    raw = _env(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(min_value, min(max_value, value))


def normalize_unicode(text: str) -> str:
    # NFKC unifies visually similar forms such as full-width Latin letters,
    # Arabic presentation forms, and compatibility characters.
    return unicodedata.normalize("NFKC", text or "")


def normalize_arabic(text: str) -> str:
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = TATWEEL_RE.sub("", text)

    # Conservative Arabic normalization for retrieval.
    # We normalize common alef variants but do not convert ة to ه because this can
    # harm readability and meaning.
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ﻻ": "لا",
        "ﻷ": "لا",
        "ﻹ": "لا",
        "ﻵ": "لا",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # Persian/Arabic-Indic digits to Western digits to improve matching.
    digit_map = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    text = text.translate(digit_map)

    return text


def normalize_punctuation(text: str) -> str:
    replacements = {
        "“": '"',
        "”": '"',
        "„": '"',
        "’": "'",
        "‘": "'",
        "—": "-",
        "–": "-",
        "…": "...",
        "،": "، ",
        "؛": "؛ ",
        "؟": "؟ ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # Remove extra spaces introduced before punctuation.
    text = re.sub(r"\s+([,.;:!?؟،؛])", r"\1", text)
    text = re.sub(r"([,.;:!?؟،؛])([^\s\n])", r"\1 \2", text)
    return text


def remove_ocr_noise_lines(text: str) -> str:
    cleaned: list[str] = []
    previous = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            cleaned.append("")
            previous = ""
            continue

        if DASH_LINE_RE.match(line):
            continue

        # Remove isolated page numbers, but keep numbered medical content because
        # those lines usually have words too.
        if PAGE_NUMBER_RE.match(line):
            continue

        # Drop very noisy symbol-only lines.
        alnum_count = sum(ch.isalnum() for ch in line)
        if len(line) >= 8 and alnum_count / max(len(line), 1) < 0.25:
            continue

        # Remove exact consecutive duplicate lines caused by OCR.
        if line == previous:
            continue

        cleaned.append(line)
        previous = line

    return "\n".join(cleaned)


def fix_common_ocr_spacing(text: str) -> str:
    # Join broken hyphenation in English: glauco-\nma -> glaucoma.
    text = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", text)

    # Join line breaks inside a sentence. We keep paragraph breaks intact.
    text = re.sub(r"(?<![.!?؟:؛])\n(?!\n|#|\s*[-*•]|\s*\d+[.)])", " ", text)

    # Normalize bullet variants.
    text = re.sub(r"^\s*[•●○▪▫]\s*", "- ", text, flags=re.MULTILINE)

    return text


def clean_for_rag(text: str) -> ProcessedText:
    original_length = len(text or "")

    level = _env("TEXT_NORMALIZATION_LEVEL", "standard").strip().lower()
    text = normalize_unicode(text)
    text = CONTROL_RE.sub(" ", text)
    text = normalize_arabic(text)
    text = normalize_punctuation(text)
    text = fix_common_ocr_spacing(text)
    text = remove_ocr_noise_lines(text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = MULTI_SPACE_RE.sub(" ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = MULTI_NEWLINE_RE.sub("\n\n", text)
    text = text.strip()

    if level == "light":
        # Light mode is already covered by the conservative steps above.
        pass
    elif level == "aggressive":
        # Optional: remove very short fragments that are usually OCR garbage.
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if s and len(s) <= 2 and not s.isdigit():
                continue
            lines.append(line)
        text = "\n".join(lines).strip()

    return ProcessedText(
        text=text,
        metadata={
            "original_length": original_length,
            "cleaned_length": len(text),
            "normalization_level": level,
        },
    )


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or _int_env("RAG_CHUNK_SIZE", 900, 300, 3000)
    overlap = overlap if overlap is not None else _int_env("RAG_CHUNK_OVERLAP", 140, 0, 800)

    text = (text or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            # Split very long paragraphs by sentence-like boundaries first.
            parts = re.split(r"(?<=[.!?؟؛])\s+", paragraph)
        else:
            parts = [paragraph]

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if not current:
                current = part
            elif len(current) + 2 + len(part) <= chunk_size:
                current += "\n\n" + part
            else:
                chunks.append(current.strip())
                if overlap > 0:
                    current = current[-overlap:].strip() + "\n\n" + part
                else:
                    current = part

    if current.strip():
        chunks.append(current.strip())

    return chunks

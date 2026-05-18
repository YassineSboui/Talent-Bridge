"""
Translation utilities for multilingual CV NER extraction.

Strategy:
  1. Detect the language of the input CV text.
  2. If non-English, translate the full text to English.
  3. Run NER on the English translation (model was trained on English).
  4. Map extracted entities back to the original text where possible,
     falling back to the translated entity text otherwise.
"""

import re
from typing import Optional

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

# Maximum chars Google Translate accepts per request
_CHUNK_SIZE = 4500


def detect_language(text: str) -> str:
    """Return ISO-639-1 code (e.g. 'en', 'fr', 'ar'). Defaults to 'en'."""
    try:
        # Use a representative sample (first 2000 chars) for speed
        sample = text[:2000]
        return detect(sample)
    except LangDetectException:
        return "en"


def _chunk_text(text: str, max_len: int = _CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split("\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > max_len and current:
            chunks.append(current)
            current = para
        else:
            current = current + "\n" + para if current else para
    if current:
        chunks.append(current)
    return chunks


def translate_text(text: str, source_lang: str, target_lang: str = "en") -> str:
    """
    Translate text from source_lang to target_lang using Google Translate.
    Handles long texts by chunking.
    """
    if source_lang == target_lang:
        return text

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    chunks = _chunk_text(text)
    translated_chunks = []
    for chunk in chunks:
        if chunk.strip():
            translated_chunks.append(translator.translate(chunk))
        else:
            translated_chunks.append(chunk)
    return "\n".join(translated_chunks)


def translate_entity(entity_text: str, source_lang: str, target_lang: str) -> str:
    """Translate a single short entity string."""
    if source_lang == target_lang or not entity_text.strip():
        return entity_text
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(entity_text)
    except Exception:
        return entity_text


def _normalize(s: str) -> str:
    """Lowercase, strip, collapse whitespace for fuzzy matching."""
    return re.sub(r"\s+", " ", s.strip().lower())


def find_original_span(entity_en: str, original_text: str,
                       translated_text: str) -> Optional[str]:
    """
    Try to find the original-language version of an English entity
    by positional mapping between translated and original text.

    Returns the original span if found, None otherwise.
    """
    en_norm = _normalize(entity_en)
    orig_norm = _normalize(original_text)

    # 1) Direct match — entity appears verbatim in original (names, emails, skills like Python)
    idx = orig_norm.find(en_norm)
    if idx != -1:
        # Extract from the actual original preserving case
        orig_flat = re.sub(r"\s+", " ", original_text.strip())
        return orig_flat[idx:idx + len(en_norm)].strip()

    # 2) Positional mapping: find entity position in translated text,
    #    then map to approximate position in original text
    trans_norm = _normalize(translated_text)
    pos_in_trans = trans_norm.find(en_norm)
    if pos_in_trans == -1:
        return None

    # Calculate relative position (0.0 to 1.0) in translated text
    ratio = pos_in_trans / max(len(trans_norm), 1)
    entity_len_ratio = len(en_norm) / max(len(trans_norm), 1)

    # Map to approximate position in original text
    orig_flat = re.sub(r"\s+", " ", original_text.strip())
    approx_start = int(ratio * len(orig_flat))
    approx_len = max(int(entity_len_ratio * len(orig_flat)), len(en_norm))

    # Extract a window around the approximate position
    window_start = max(0, approx_start - approx_len)
    window_end = min(len(orig_flat), approx_start + approx_len * 2)
    return orig_flat[window_start:window_end].strip() if window_end > window_start else None

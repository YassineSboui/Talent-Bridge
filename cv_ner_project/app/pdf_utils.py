"""
PDF text extraction utilities.

Uses PyMuPDF (fitz) for robust PDF text extraction.
Includes post-processing to clean OCR / PDF extraction artifacts.
"""

import re
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes.
    Uses PyMuPDF with multiple strategies for best quality.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages_text = []
    for page in doc:
        # Strategy 1: Standard text extraction (preserves layout better)
        text = page.get_text("text")

        # Strategy 2: If text is very short, try blocks extraction
        if len(text.strip()) < 50:
            blocks = page.get_text("blocks")
            text = "\n".join(
                block[4] for block in sorted(blocks, key=lambda b: (b[1], b[0]))
                if block[-1] == 0  # text blocks only
            )

        pages_text.append(text)

    doc.close()
    full_text = "\n".join(pages_text)
    return clean_extracted_text(full_text)


def clean_extracted_text(text: str) -> str:
    """
    Clean common PDF extraction artifacts.
    """
    # Fix common ligature issues
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": " ",  # bullet
        "\u00a0": " ",  # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Collapse excessive whitespace (but keep single newlines for structure)
    text = re.sub(r"[ \t]+", " ", text)  # collapse horizontal space
    text = re.sub(r"\n{3,}", "\n\n", text)  # max 2 consecutive newlines
    text = re.sub(r" *\n *", "\n", text)  # strip spaces around newlines

    # Remove null bytes and control characters (except newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()

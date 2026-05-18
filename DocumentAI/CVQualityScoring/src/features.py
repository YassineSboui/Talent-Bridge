from __future__ import annotations

import re
import unicodedata
from typing import Any


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?){2,5}\d{1,4}")
URL_RE = re.compile(r"(?:linkedin\.com|github\.com|https?://|www\.)", re.IGNORECASE)
DATE_SIGNAL_RE = re.compile(r"\b(?:19\d{2}|20\d{2}|present|current|aujourd hui|actuel|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", re.IGNORECASE)
QUANTIFIED_IMPACT_RE = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s?%|\d+\s?(?:users?|clients?|projects?|dashboards?|reports?|apis?|kpis?|hours?|days?))\b",
    re.IGNORECASE,
)

SECTION_PATTERNS = {
    "skills": re.compile(r"\b(skills?|competences?|competences techniques|technologies|outils)\b", re.IGNORECASE),
    "education": re.compile(r"\b(education|formation|diplome|degree|licence|master|bachelor|university|universite|ecole)\b", re.IGNORECASE),
    "experience": re.compile(r"\b(experience|work experience|professional experience|stage|internship|emploi|poste)\b", re.IGNORECASE),
    "projects": re.compile(r"\b(projects?|projets?|portfolio|realisations?)\b", re.IGNORECASE),
    "languages": re.compile(r"\b(languages?|langues?)\b", re.IGNORECASE),
    "certifications": re.compile(r"\b(certifications?|certificats?)\b", re.IGNORECASE),
}


def extract_quality_features(text: str, extraction: dict[str, Any]) -> dict[str, Any]:
    tokens = re.findall(r"\b\w+\b", text)
    words = [token for token in tokens if len(token) > 1]
    short_tokens = [token for token in tokens if len(token) <= 1]
    noise_ratio = len(short_tokens) / max(len(tokens), 1)
    repeated_line_ratio = repeated_line_ratio_for(text)
    bullet_line_count = bullet_line_count_for(text)
    detected_sections = {name: bool(pattern.search(text)) for name, pattern in SECTION_PATTERNS.items()}

    has_email = bool(extraction.get("email_addresses")) or bool(EMAIL_RE.search(text))
    has_phone = bool(PHONE_RE.search(text))
    has_profile_link = bool(extraction.get("linkedin")) or bool(extraction.get("github")) or bool(URL_RE.search(text))
    text_length = len(text)

    return {
        "has_email": has_email,
        "has_phone": has_phone,
        "has_profile_link": has_profile_link,
        "has_skills_section": detected_sections["skills"] or bool(extraction.get("skills")),
        "has_education_section": detected_sections["education"] or bool(extraction.get("degrees")) or bool(extraction.get("colleges")),
        "has_experience_or_projects": detected_sections["experience"] or detected_sections["projects"] or bool(extraction.get("companies")),
        "has_languages_section": detected_sections["languages"] or bool(extraction.get("languages")),
        "has_certifications_section": detected_sections["certifications"],
        "section_count": sum(1 for found in detected_sections.values() if found),
        "core_section_count": sum(
            1 for found in [
                detected_sections["skills"] or bool(extraction.get("skills")),
                detected_sections["education"] or bool(extraction.get("degrees")) or bool(extraction.get("colleges")),
                detected_sections["experience"] or detected_sections["projects"] or bool(extraction.get("companies")),
            ] if found
        ),
        "text_length": text_length,
        "word_count": len(words),
        "text_length_ok": 550 <= text_length <= 12000,
        "text_too_short": text_length < 350,
        "text_too_long": text_length > 12000,
        "noise_ratio": round(noise_ratio, 4),
        "low_noise": noise_ratio <= 0.18,
        "repeated_line_ratio": round(repeated_line_ratio, 4),
        "low_repetition": repeated_line_ratio <= 0.25,
        "bullet_line_count": bullet_line_count,
        "has_professional_dates": bool(DATE_SIGNAL_RE.search(text)),
        "has_quantified_impact": bool(QUANTIFIED_IMPACT_RE.search(text)),
    }


def normalize_cv_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text or "").strip().lower()
    return "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))


def repeated_line_ratio_for(text: str) -> float:
    lines = [line.strip().lower() for line in text.splitlines() if len(line.strip()) >= 15]
    if not lines:
        return 0.0
    return 1.0 - (len(set(lines)) / len(lines))


def bullet_line_count_for(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\s*(?:[-*]|\u2022|\d+[.)])\s+", line))

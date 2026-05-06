"""Importable feature selectors for the CV quality model artifact."""

from __future__ import annotations


FEATURE_NAMES = [
    "has_email",
    "has_phone",
    "has_profile_link",
    "has_skills_section",
    "has_education_section",
    "has_experience_or_projects",
    "has_languages_section",
    "has_certifications_section",
    "section_count",
    "core_section_count",
    "text_length",
    "word_count",
    "noise_ratio",
    "low_noise",
    "repeated_line_ratio",
    "low_repetition",
    "bullet_line_count",
    "has_professional_dates",
    "has_quantified_impact",
]


def text_selector(items: list[dict]) -> list[str]:
    return [item["text"] for item in items]


def numeric_selector(items: list[dict]) -> list[list[float]]:
    matrix = []
    for item in items:
        features = item["features"]
        matrix.append([float(features.get(name, 0) or 0) for name in FEATURE_NAMES])
    return matrix

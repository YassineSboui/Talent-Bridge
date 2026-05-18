"""CV quality grade helpers."""

from __future__ import annotations


GRADE_THRESHOLDS = [
    (90, "Excellent"),
    (75, "Good"),
    (55, "Average"),
    (35, "Weak"),
    (0, "Poor"),
]


def grade_from_score(score: float | int) -> str:
    numeric_score = max(0, min(float(score), 100))
    for threshold, grade in GRADE_THRESHOLDS:
        if numeric_score >= threshold:
            return grade
    return "Poor"


def binary_label_from_grade(grade: str) -> str:
    return "Pro" if grade in {"Excellent", "Good"} else "Non Pro"

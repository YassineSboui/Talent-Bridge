"""Rule-based CV quality and structure classifier.

This baseline is intentionally deterministic. It gives useful feedback now and
also creates feature signals that can be reused later by a deep learning model.
"""

from __future__ import annotations

from typing import Any

from .features import extract_quality_features, normalize_cv_text
from .model_loader import predict_with_trained_model
from .rules import add_score, bounded_score, decision_confidence, quality_hard_gates


def classify_cv_quality(text: str, extraction: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify CV quality as Pro or Non Pro with explanations."""
    extraction = extraction or {}
    normalized = normalize_cv_text(text)
    features = extract_quality_features(normalized, extraction)
    model_prediction = predict_with_trained_model(normalized, features)
    hard_gates = quality_hard_gates(features)

    positive_checks: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []
    score = 0

    score += add_score(features["has_email"], 15, "Has email contact", "Missing email contact", positive_checks, issues)
    score += add_score(features["has_phone"], 10, "Has phone contact", "Missing phone contact", positive_checks, issues)
    score += add_score(features["has_skills_section"], 15, "Has skills section", "Missing clear skills section", positive_checks, issues)
    score += add_score(features["has_education_section"], 15, "Has education section", "Missing clear education section", positive_checks, issues)
    score += add_score(features["has_experience_or_projects"], 15, "Has experience or projects", "Missing experience or projects section", positive_checks, issues)
    score += add_score(features["has_profile_link"], 8, "Has profile or portfolio link", "Missing LinkedIn, GitHub, or portfolio link", positive_checks, issues)
    score += add_score(features["text_length_ok"], 10, "Text length is acceptable", "CV text is too short or too long", positive_checks, issues)
    score += add_score(features["section_count"] >= 4, 7, "Has multiple clear sections", "CV structure has too few recognizable sections", positive_checks, issues)
    score += add_score(features["low_noise"], 3, "Low extraction noise", "Text extraction looks noisy", positive_checks, issues)
    score += add_score(features["low_repetition"], 2, "Low repeated content", "CV appears to contain repeated content", positive_checks, issues)
    score += add_score(features["has_professional_dates"], 3, "Has dates or timeline evidence", "Missing dates or timeline evidence", positive_checks, issues)
    score += add_score(features["has_quantified_impact"], 2, "Has quantified impact", "No quantified impact found", positive_checks, issues)

    if not features["has_email"]:
        suggestions.append("Add a professional email address near the top of the CV.")
    if not features["has_phone"]:
        suggestions.append("Add a phone number near the contact information.")
    if not features["has_skills_section"]:
        suggestions.append("Add a dedicated skills section with technical and soft skills.")
    if not features["has_education_section"]:
        suggestions.append("Add an education section with degree, school, and dates.")
    if not features["has_experience_or_projects"]:
        suggestions.append("Add professional experience, internships, or academic/personal projects.")
    if not features["has_profile_link"]:
        suggestions.append("Add a LinkedIn, GitHub, portfolio, or project link if available.")
    if not features["text_length_ok"]:
        suggestions.append("Keep the CV detailed enough to evaluate, but avoid excessive repeated text.")
    if not features["low_noise"]:
        suggestions.append("Export the CV as a clean text-based PDF to improve automatic analysis.")
    if not features["low_repetition"]:
        suggestions.append("Remove duplicated sections or repeated content from the CV.")
    if not features["has_professional_dates"]:
        suggestions.append("Add dates for education, internships, jobs, or projects.")
    if not features["has_quantified_impact"]:
        suggestions.append("Add measurable impact where possible, such as percentages, dashboards, reports, users, or projects delivered.")
    for gate in hard_gates:
        if gate not in issues:
            issues.append(gate)

    structure_score = bounded_score(
        20 * features["has_skills_section"]
        + 20 * features["has_education_section"]
        + 20 * features["has_experience_or_projects"]
        + 20 * (features["section_count"] >= 4)
        + 10 * features["low_noise"]
        + 10 * features["low_repetition"]
    )
    content_score = bounded_score(
        20 * bool(extraction.get("skills"))
        + 15 * bool(extraction.get("degrees"))
        + 15 * bool(extraction.get("languages"))
        + 20 * (features["has_email"] or features["has_phone"])
        + 15 * features["text_length_ok"]
        + 15 * features["has_profile_link"]
    )

    score = bounded_score(score)
    rule_label = "Pro" if score >= 70 else "Non Pro"
    quality_label = rule_label
    decision_source = "rules"
    if hard_gates:
        quality_label = "Non Pro"
        decision_source = "hard_gates"
        score = min(score, 69)
    elif model_prediction and model_prediction["confidence"] >= 0.85:
        # The trained model is useful as a second opinion, but current labels are
        # bootstrap/weak. It can confirm rules or resolve borderline scores; it
        # should not flip an obviously good/bad rule decision.
        decision_source = "hybrid_model"
        if model_prediction["label"] == rule_label:
            score = int(round((score * 0.78) + (model_prediction["confidence"] * 100 * 0.22)))
        elif 60 <= score <= 79:
            quality_label = model_prediction["label"]
            score = int(round((score * 0.82) + (model_prediction["confidence"] * 100 * 0.18)))
        else:
            decision_source = "rules_model_disagreed"

    return {
        "quality_label": quality_label,
        "quality_score": score,
        "rule_label": rule_label,
        "decision_source": decision_source,
        "hard_gates": hard_gates,
        "structure_score": structure_score,
        "content_score": content_score,
        "model_prediction": model_prediction,
        "confidence": decision_confidence(score, hard_gates, model_prediction, rule_label, quality_label),
        "features": features,
        "positive_checks": positive_checks,
        "issues": issues,
        "suggestions": suggestions[:8],
    }

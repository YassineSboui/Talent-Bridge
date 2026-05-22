from __future__ import annotations


def quality_hard_gates(features: dict) -> list[str]:
    """Return severe CV issues that force or cap a Non Pro decision."""
    gates = []
    if features["text_too_short"]:
        gates.append("CV text is too short to be considered professional.")
    if not features["has_email"] and not features["has_phone"]:
        gates.append("CV has no reliable contact information.")
    if features["core_section_count"] < 2:
        gates.append("CV is missing most core sections: skills, education, experience/projects.")
    if not features["low_noise"] and features["noise_ratio"] > 0.30:
        gates.append("CV text extraction is too noisy for reliable screening.")
    if not features["low_repetition"] and features["repeated_line_ratio"] > 0.45:
        gates.append("CV contains too much repeated content.")
    return gates


def add_score(condition: bool, points: int, positive: str, issue: str, positive_checks: list[str], issues: list[str]) -> int:
    """Add rule points and record either a positive check or issue."""
    if condition:
        positive_checks.append(positive)
        return points
    issues.append(issue)
    return 0


def bounded_score(value: float) -> int:
    """Clamp a score to the inclusive 0-100 integer range."""
    return int(max(0, min(round(value), 100)))


def decision_confidence(score: int, hard_gates: list[str], model_prediction: dict | None, rule_label: str, quality_label: str) -> float:
    """Estimate confidence from score distance, hard gates, and model agreement."""
    distance = abs(score - 70) / 30
    confidence = min(0.98, 0.62 + max(0, distance) * 0.22)
    if hard_gates:
        confidence = max(confidence, 0.9)
    if model_prediction and model_prediction.get("label") == quality_label:
        confidence = min(0.99, (confidence + float(model_prediction.get("confidence", 0.7))) / 2)
    if rule_label != quality_label:
        confidence = min(confidence, 0.82)
    return round(confidence, 4)

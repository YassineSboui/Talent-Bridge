from __future__ import annotations


def build_explanation(
    matched_skills: list[str],
    missing_skills: list[str],
    role_score: float,
    experience_score: float,
    education_score: float,
    location_score: float,
    opportunity_score: float,
    skills_score: float,
    semantic_score: float,
    job_skills: list[str],
) -> list[str]:
    """Generate human-readable reasons behind a job match score."""
    explanation = []
    if matched_skills:
        explanation.append(f"Matched {len(matched_skills)} skills: {', '.join(matched_skills[:8])}")
    else:
        explanation.append("No direct skill overlap found")
    if missing_skills:
        explanation.append(f"Missing {len(missing_skills)} listed job skills")
    if semantic_score >= 75:
        explanation.append("High NLP semantic similarity between CV profile and job text")
    elif semantic_score >= 55:
        explanation.append("Moderate NLP semantic similarity between CV profile and job text")
    elif semantic_score < 30:
        explanation.append("Low NLP semantic similarity between CV profile and job text")
    if job_skills and skills_score < 50:
        explanation.append("Skill evidence is limited; score was capped to avoid a weak false-positive match")
    elif not job_skills:
        explanation.append("Job listing has no structured skills, so matching relies mostly on role fit")
    if role_score >= 100:
        explanation.append("Exact role category match")
    elif role_score >= 60:
        explanation.append("Related role category match")
    elif role_score <= 0:
        explanation.append("Role category is not aligned with the target role")
    if experience_score >= 90:
        explanation.append("Experience level is compatible")
    elif experience_score < 60:
        explanation.append("Experience level may be too low for this job")
    if education_score >= 90:
        explanation.append("Education requirements look compatible")
    if location_score >= 100:
        explanation.append("Location or remote preference matches")
    elif location_score == 0:
        explanation.append("Remote preference does not match")
    if opportunity_score >= 60:
        explanation.append("Strong opportunity signals: salary, remote, no-degree, or insurance")
    return explanation

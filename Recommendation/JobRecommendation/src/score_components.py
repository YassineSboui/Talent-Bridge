from __future__ import annotations

import re
from typing import Any

from NLP.SkillExtraction.src.normalization import normalize_text


SENIORITY_ORDER = {
    "intern": 0,
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
}

RELATED_ROLES = {
    "data analyst": {"business analyst", "senior data analyst"},
    "business analyst": {"data analyst", "senior data analyst"},
    "data scientist": {"machine learning engineer", "senior data scientist"},
    "machine learning engineer": {"data scientist", "software engineer"},
    "data engineer": {"senior data engineer", "cloud engineer"},
    "senior data analyst": {"data analyst", "business analyst"},
    "senior data scientist": {"data scientist", "machine learning engineer"},
    "senior data engineer": {"data engineer", "cloud engineer"},
    "cloud engineer": {"data engineer", "senior data engineer"},
    "software engineer": {"machine learning engineer"},
}

ROLE_CORE_SKILLS = {
    "data analyst": {"sql", "excel", "power bi", "tableau", "python", "statistics", "data analysis", "looker studio"},
    "business analyst": {"sql", "excel", "power bi", "tableau", "business analysis", "jira", "scrum", "data analysis"},
    "data scientist": {"python", "sql", "machine learning", "statistics", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"},
    "machine learning engineer": {"python", "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "docker", "kubernetes"},
    "data engineer": {"sql", "python", "spark", "airflow", "kafka", "hadoop", "azure", "aws", "gcp"},
    "cloud engineer": {"azure", "aws", "gcp", "docker", "kubernetes", "terraform", "linux", "ci/cd", "devops"},
    "software engineer": {"python", "java", "javascript", "typescript", "react", "vue", "node.js", "spring boot", "docker", "sql"},
}

LOW_SIGNAL_SKILLS = {
    "css", "html", "html5", "css3", "jira", "scrum", "oracle", "mysql", "linux", "github", "gitlab",
    "bootstrap", "framework", "others", "monitoring",
}


def score_skills(candidate_skills: list[str], job_skills: list[str], target_role: str | None, role_score: float) -> float:
    """Score direct skill overlap and role-core skill coverage."""
    candidate_set = set(candidate_skills)
    job_set = set(job_skills)
    matched = candidate_set & job_set
    core_skills = core_skills_for_role(target_role)
    core_coverage = role_core_coverage(candidate_set, core_skills)

    if not job_set:
        if role_score >= 80:
            return round(45.0 * core_coverage, 2)
        return 0.0

    direct_coverage = len(matched) / len(job_set)
    score = 100.0 * ((0.72 * direct_coverage) + (0.28 * core_coverage))

    if len(job_set) <= 2:
        score = min(score, 72.0 if role_score >= 80 else 52.0)
    if matched and matched <= LOW_SIGNAL_SKILLS:
        score = min(score, 42.0)
    if target_role and core_coverage < 0.35:
        score = min(score, 64.0)
    if not matched:
        score = min(score, 28.0 if role_score >= 80 else 10.0)
    return round(score, 2)


def apply_match_caps(raw_score: float, skills_score: float, role_score: float, matched_skills: list[str], job_skills: list[str], target_role: str | None) -> float:
    """Cap weak matches so role text alone cannot create false positives."""
    score = raw_score
    matched_set = set(matched_skills)
    core_matches = matched_set & core_skills_for_role(target_role)

    if role_score >= 80 and skills_score < 35:
        score = min(score, 62.0)
    elif role_score >= 80 and skills_score < 50:
        score = min(score, 72.0)
    if job_skills and not matched_skills:
        score = min(score, 58.0)
    if job_skills and len(matched_skills) == 1:
        score = min(score, 68.0 if core_matches else 58.0)
    if job_skills and matched_set and matched_set <= LOW_SIGNAL_SKILLS:
        score = min(score, 55.0)
    if target_role and role_score < 60:
        score = min(score, 59.0)
    return score


def score_role(target_role: str | None, category_name: str | None, job_title: str | None) -> float:
    """Score how well a job title/category matches the candidate target role."""
    if not target_role:
        return 70.0
    target = normalize_text(target_role)
    category = normalize_text(category_name)
    title = normalize_text(job_title)
    if target and target == category:
        return 100.0
    if target and target in title:
        return 95.0
    if target and category in RELATED_ROLES.get(target, set()):
        return 70.0
    target_tokens = set(target.split())
    title_tokens = set(title.split())
    if target_tokens and len(target_tokens & title_tokens) >= max(1, len(target_tokens) - 1):
        return 75.0
    return 0.0


def infer_job_seniority(job_title: str | None, category_name: str | None = None) -> str:
    """Infer required seniority level from job title and category text."""
    text = normalize_text(" ".join(value for value in [job_title, category_name] if value))
    if re.search(r"\b(intern|internship|stage|stagiaire|trainee|apprentice|alternance)\b", text):
        return "intern"
    if re.search(r"\b(junior|jr|entry level|entry-level|assistant)\b", text):
        return "junior"
    if re.search(r"\b(lead|principal|manager|architect|head|director)\b", text):
        return "lead"
    if re.search(r"\b(senior|sr|experienced|expert)\b", text):
        return "senior"
    return "unspecified"


def score_experience(candidate_level: str | None, job_title: str | None, category_name: str | None) -> float:
    """Score candidate seniority compatibility with inferred job seniority."""
    if not candidate_level:
        return 70.0
    job_level = infer_job_seniority(job_title, category_name)
    if job_level == "unspecified":
        return 100.0 if candidate_level in {"junior", "mid", "senior"} else 85.0
    diff = SENIORITY_ORDER[candidate_level] - SENIORITY_ORDER[job_level]
    if diff == 0:
        return 100.0
    if diff > 0:
        return 90.0
    if diff == -1:
        return 60.0
    return 20.0


def score_education(candidate_degrees: list[str], no_degree_mention: Any) -> float:
    """Score education compatibility using extracted degrees and job flags."""
    if candidate_degrees:
        return 100.0
    if bool(no_degree_mention):
        return 90.0
    return 60.0


def score_location(preferred_country: str | None, remote_preference: str, job: dict[str, Any], remote_only: str, remote_onsite: str) -> float:
    """Score country and remote-work preference alignment."""
    is_remote = bool(job.get("is_work_from_home"))
    if remote_preference == remote_only:
        return 100.0 if is_remote else 0.0
    if remote_preference == remote_onsite and is_remote:
        return 60.0
    if not preferred_country:
        return 70.0
    return 100.0 if normalize_text(preferred_country) == normalize_text(job.get("country")) else 30.0


def score_opportunity(job: dict[str, Any]) -> float:
    """Score positive job opportunity signals such as salary and remote work."""
    score = 0.0
    if bool(job.get("has_salary_info")):
        score += 40.0
    if bool(job.get("is_work_from_home")):
        score += 25.0
    if bool(job.get("no_degree_mention")):
        score += 20.0
    if bool(job.get("has_health_insurance")):
        score += 15.0
    return min(score, 100.0)


def core_skills_for_role(target_role: str | None) -> set[str]:
    """Return canonical core skills for a target role when known."""
    target = normalize_text(target_role)
    if target in ROLE_CORE_SKILLS:
        return ROLE_CORE_SKILLS[target]
    for role, skills in ROLE_CORE_SKILLS.items():
        if role in target or target in role:
            return skills
    return set()


def role_core_coverage(candidate_skills: set[str], core_skills: set[str]) -> float:
    """Estimate how many role-critical skills the candidate already has."""
    if not core_skills:
        return 0.5
    required = min(5, len(core_skills))
    return min(1.0, len(candidate_skills & core_skills) / required)

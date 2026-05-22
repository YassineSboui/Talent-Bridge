"""Job matching against the SQL Server data warehouse."""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass
from typing import Any

from NLP.SkillExtraction.src.normalization import normalize_skills, normalize_text, split_csv_values
from .explainer import build_explanation
from .score_components import (
    RELATED_ROLES,
    ROLE_CORE_SKILLS,
    LOW_SIGNAL_SKILLS,
    SENIORITY_ORDER,
    apply_match_caps,
    core_skills_for_role,
    infer_job_seniority,
    role_core_coverage,
    score_education,
    score_experience,
    score_location,
    score_opportunity,
    score_role,
    score_skills,
)
from .semantic_similarity import candidate_semantic_text, semantic_similarity_scores


DEFAULT_SQL_CONNECTION_STRING = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=DW_DataJobs;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

REMOTE_ANY = "any"
REMOTE_ONLY = "remote_only"
REMOTE_ONSITE = "onsite_or_hybrid"

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


@dataclass
class CandidateProfile:
    """Normalized candidate profile used by the matching engine."""

    name: str | None
    email: str | None
    target_role: str | None
    preferred_country: str | None
    remote_preference: str
    years_of_experience: float | None
    seniority_level: str | None
    skills: list[str]
    degrees: list[str]
    languages: list[str]
    linkedin: str | None
    github: str | None
    semantic_text: str


def build_candidate_profile(
    extraction: dict[str, Any],
    target_role: str | None = None,
    preferred_country: str | None = None,
    remote_preference: str = REMOTE_ANY,
) -> CandidateProfile:
    """Convert CV extraction output to a normalized profile for matching."""
    years = infer_years_of_experience(extraction.get("years_of_experience", []))
    return CandidateProfile(
        name=_first(extraction.get("name")),
        email=_first(extraction.get("email_addresses")),
        target_role=target_role.strip() if target_role else None,
        preferred_country=preferred_country.strip() if preferred_country else None,
        remote_preference=remote_preference if remote_preference in {REMOTE_ANY, REMOTE_ONLY, REMOTE_ONSITE} else REMOTE_ANY,
        years_of_experience=years,
        seniority_level=infer_candidate_seniority(years),
        skills=normalize_skills(extraction.get("skills", [])),
        degrees=[normalize_text(value) for value in extraction.get("degrees", []) if normalize_text(value)],
        languages=[normalize_text(value) for value in extraction.get("languages", []) if normalize_text(value)],
        linkedin=extraction.get("linkedin"),
        github=extraction.get("github"),
        semantic_text=candidate_semantic_text(extraction, target_role),
    )


def fetch_jobs_from_sql(
    target_role: str | None = None,
    max_candidates: int = 5000,
) -> list[dict[str, Any]]:
    """Load candidate jobs from dbo.vw_job_matching.

    The endpoint deliberately fetches a bounded candidate set, then ranks it in
    Python so the score remains transparent and easy to explain.
    """
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL Server matching. Install requirements.txt first.") from exc

    max_candidates = max(1, min(int(max_candidates), 50000))
    connection_string = os.getenv("DW_DATAJOBS_CONNECTION_STRING", DEFAULT_SQL_CONNECTION_STRING)
    where_sql = ""
    params: list[Any] = []

    if target_role:
        like_role = f"%{target_role}%"
        where_sql = "WHERE category_name = ? OR job_title LIKE ?"
        params.extend([target_role, like_role])

    query = f"""
        SELECT TOP ({max_candidates})
            job_posting_key,
            job_title,
            category_name,
            company_name,
            country,
            city,
            is_work_from_home,
            no_degree_mention,
            has_health_insurance,
            salary_year_avg,
            salary_hour_avg,
            has_salary_info,
            portal_name,
            posted_date,
            skills_csv,
            skill_categories_csv,
            schedule_types_csv
        FROM dbo.vw_job_matching
        {where_sql}
        ORDER BY has_salary_info DESC, posted_date DESC, job_posting_key DESC;
    """

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def list_saved_analyses(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent saved CV analyses from SQL Server."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL Server access. Install requirements.txt first.") from exc

    limit = max(1, min(int(limit), 500))
    connection_string = os.getenv("DW_DATAJOBS_CONNECTION_STRING", DEFAULT_SQL_CONNECTION_STRING)
    query = f"""
        SELECT TOP ({limit})
            analysis_id,
            created_at,
            file_name,
            candidate_name,
            target_role,
            preferred_country,
            remote_preference,
            years_of_experience,
            seniority_level,
            quality_label,
            quality_score,
            extracted_skill_count,
            saved_match_count,
            best_match_score,
            avg_match_score
        FROM cv.vw_analysis_summary
        ORDER BY analysis_id DESC;
    """
    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [_sql_row_to_dict(columns, row) for row in cursor.fetchall()]


def get_saved_analysis(analysis_id: int) -> dict[str, Any] | None:
    """Return one saved analysis with candidate skills and match details."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL Server access. Install requirements.txt first.") from exc

    connection_string = os.getenv("DW_DATAJOBS_CONNECTION_STRING", DEFAULT_SQL_CONNECTION_STRING)
    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                analysis_id,
                created_at,
                file_name,
                candidate_name,
                email,
                target_role,
                preferred_country,
                remote_preference,
                years_of_experience,
                seniority_level,
                quality_label,
                quality_score,
                structure_score,
                content_score,
                extracted_skill_count,
                saved_match_count,
                best_match_score,
                avg_match_score
            FROM cv.vw_analysis_summary
            WHERE analysis_id = ?;
            """,
            analysis_id,
        )
        row = cursor.fetchone()
        if not row:
            return None
        summary = _sql_row_to_dict([column[0] for column in cursor.description], row)

        cursor.execute(
            """
            SELECT skill_name
            FROM cv.vw_candidate_skill
            WHERE analysis_id = ?
            ORDER BY skill_name;
            """,
            analysis_id,
        )
        skills = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT
                rank_num,
                job_posting_key,
                job_title,
                category_name,
                company_name,
                country,
                city,
                is_work_from_home,
                has_salary_info,
                salary_year_avg,
                match_score,
                skills_score,
                role_score,
                experience_score,
                education_score,
                location_score,
                opportunity_score,
                matched_skills_csv,
                missing_skills_csv,
                explanation
            FROM cv.vw_match_detail
            WHERE analysis_id = ?
            ORDER BY rank_num;
            """,
            analysis_id,
        )
        columns = [column[0] for column in cursor.description]
        matches = [_sql_row_to_dict(columns, row) for row in cursor.fetchall()]

    return {"summary": summary, "skills": skills, "matches": matches}


def rank_jobs(
    candidate: CandidateProfile,
    jobs: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Score and rank jobs for one candidate profile."""
    semantic_scores = semantic_similarity_scores(candidate.semantic_text, jobs)
    scored = [score_job(candidate, job, semantic_scores[index]) for index, job in enumerate(jobs)]
    scored.sort(key=lambda item: item["match_score"], reverse=True)
    return scored[: max(1, min(int(limit), 100))]


def save_analysis_results(
    candidate: CandidateProfile,
    extraction: dict[str, Any],
    quality: dict[str, Any] | None,
    matches: list[dict[str, Any]],
    file_name: str | None = None,
) -> int:
    """Persist one CV analysis and its match results to the cv.* SQL tables."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL Server persistence. Install requirements.txt first.") from exc

    connection_string = os.getenv("DW_DATAJOBS_CONNECTION_STRING", DEFAULT_SQL_CONNECTION_STRING)
    quality = quality or {}
    extraction_json = json.dumps(extraction, ensure_ascii=False, default=str)
    quality_json = json.dumps(quality, ensure_ascii=False, default=str)

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        row = cursor.execute(
            """
            INSERT INTO cv.analysis_run (
                file_name,
                candidate_name,
                email,
                target_role,
                preferred_country,
                remote_preference,
                years_of_experience,
                seniority_level,
                quality_label,
                quality_score,
                structure_score,
                content_score,
                raw_extraction_json,
                quality_json
            )
            OUTPUT INSERTED.analysis_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            file_name,
            candidate.name,
            candidate.email,
            candidate.target_role,
            candidate.preferred_country,
            candidate.remote_preference,
            candidate.years_of_experience,
            candidate.seniority_level,
            quality.get("quality_label"),
            quality.get("quality_score"),
            quality.get("structure_score"),
            quality.get("content_score"),
            extraction_json,
            quality_json,
        ).fetchone()
        analysis_id = int(row[0])

        for skill in candidate.skills:
            cursor.execute(
                "INSERT INTO cv.analysis_skill (analysis_id, skill_name) VALUES (?, ?);",
                analysis_id,
                skill,
            )

        for rank_num, match in enumerate(matches, start=1):
            breakdown = match.get("score_breakdown", {})
            cursor.execute(
                """
                INSERT INTO cv.job_match_result (
                    analysis_id,
                    rank_num,
                    job_posting_key,
                    match_score,
                    skills_score,
                    role_score,
                    experience_score,
                    education_score,
                    location_score,
                    opportunity_score,
                    matched_skills_csv,
                    missing_skills_csv,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                analysis_id,
                rank_num,
                match.get("job_id"),
                match.get("match_score"),
                breakdown.get("skills"),
                breakdown.get("role"),
                breakdown.get("experience"),
                breakdown.get("education"),
                breakdown.get("location"),
                breakdown.get("opportunity"),
                ",".join(match.get("matched_skills", [])),
                ",".join(match.get("missing_skills", [])),
                " | ".join(match.get("explanation", [])),
            )

        connection.commit()
        return analysis_id


def score_job(candidate: CandidateProfile, job: dict[str, Any], semantic_score: float = 0.0) -> dict[str, Any]:
    """Score one SQL job row and return an explainable match object."""
    job_skills = normalize_skills(split_csv_values(job.get("skills_csv")))
    matched_skills = sorted(set(candidate.skills) & set(job_skills))
    missing_skills = sorted(set(job_skills) - set(candidate.skills))

    role_score = score_role(candidate.target_role, job.get("category_name"), job.get("job_title"))
    skills_score = score_skills(candidate.skills, job_skills, candidate.target_role, role_score)
    experience_score = score_experience(candidate.seniority_level, job.get("job_title"), job.get("category_name"))
    education_score = score_education(candidate.degrees, job.get("no_degree_mention"))
    location_score = score_location(candidate.preferred_country, candidate.remote_preference, job, REMOTE_ONLY, REMOTE_ONSITE)
    opportunity_score = score_opportunity(job)

    raw_score = (
        0.35 * skills_score
        + 0.25 * semantic_score
        + 0.15 * role_score
        + 0.10 * experience_score
        + 0.05 * education_score
        + 0.05 * location_score
        + 0.05 * opportunity_score
    )
    final_score = apply_match_caps(
        raw_score,
        skills_score,
        role_score,
        matched_skills,
        job_skills,
        candidate.target_role,
    )

    return {
        "job_id": job.get("job_posting_key"),
        "job_title": job.get("job_title"),
        "category": job.get("category_name"),
        "company": job.get("company_name"),
        "country": job.get("country"),
        "city": job.get("city"),
        "remote": bool(job.get("is_work_from_home")),
        "salary_year_avg": _number_or_none(job.get("salary_year_avg")),
        "salary_hour_avg": _number_or_none(job.get("salary_hour_avg")),
        "portal": job.get("portal_name"),
        "posted_date": str(job.get("posted_date")) if job.get("posted_date") is not None else None,
        "match_score": round(final_score, 2),
        "score_breakdown": {
            "skills": round(skills_score, 2),
            "semantic": round(semantic_score, 2),
            "role": round(role_score, 2),
            "experience": round(experience_score, 2),
            "education": round(education_score, 2),
            "location": round(location_score, 2),
            "opportunity": round(opportunity_score, 2),
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:20],
        "job_skills": job_skills[:40],
        "schedule_types": split_csv_values(job.get("schedule_types_csv")),
        "explanation": build_explanation(
            matched_skills,
            missing_skills,
            role_score,
            experience_score,
            education_score,
            location_score,
            opportunity_score,
            skills_score,
            semantic_score,
            job_skills,
        ),
    }


def infer_years_of_experience(values: list[str] | tuple[str, ...] | None) -> float | None:
    """Parse NER years-of-experience strings into one numeric estimate."""
    candidates = []
    for value in values or []:
        text = normalize_text(value)
        for match in re.finditer(r"(\d+(?:\.\d+)?)", text):
            number = float(match.group(1))
            if 0 <= number <= 50:
                candidates.append(number)
    return max(candidates) if candidates else None


def infer_candidate_seniority(years: float | None) -> str | None:
    """Convert years of experience into a coarse candidate seniority label."""
    if years is None:
        return None
    if years < 1:
        return "intern"
    if years < 3:
        return "junior"
    if years < 5:
        return "mid"
    if years < 8:
        return "senior"
    return "lead"


def _first(values: list[str] | tuple[str, ...] | None) -> str | None:
    """Return the first extracted value from a list-like field."""
    return values[0] if values else None


def _number_or_none(value: Any) -> float | None:
    """Convert a value to float when possible, otherwise return None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sql_row_to_dict(columns: list[str], row: Any) -> dict[str, Any]:
    """Convert a pyodbc SQL row into a JSON-friendly dictionary."""
    result = {}
    for column, value in zip(columns, row):
        if hasattr(value, "isoformat"):
            result[column] = value.isoformat()
        elif hasattr(value, "__float__") and value.__class__.__module__ == "decimal":
            result[column] = float(value)
        else:
            result[column] = value
    return result

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from Recommendation.JobRecommendation.src.matching import build_candidate_profile, rank_jobs

from ..security import current_user, require_role
from ..store import store


router = APIRouter(prefix="/matching", tags=["Matching"])


def platform_job_to_matching_job(job: dict) -> dict:
    return {
        "job_posting_key": job["id"],
        "job_title": job["title"],
        "category_name": job["category"],
        "company_name": store.companies.get(job["company_id"], {}).get("name"),
        "country": job.get("country"),
        "city": job.get("city"),
        "is_work_from_home": job.get("remote"),
        "no_degree_mention": False,
        "has_health_insurance": False,
        "salary_year_avg": job.get("salary_year_avg"),
        "salary_hour_avg": None,
        "has_salary_info": job.get("salary_year_avg") is not None,
        "portal_name": "Talent Bridge",
        "posted_date": job.get("created_at"),
        "skills_csv": ",".join(job.get("required_skills", [])),
        "skill_categories_csv": "",
        "schedule_types_csv": job.get("schedule_type"),
    }


@router.get("/candidates/me/jobs")
def candidate_job_matches(user: dict = Depends(require_role("candidate"))):
    profile = store.candidate_profiles.get(user["id"], {})
    extraction = {"name": [user["full_name"]], "email_addresses": [user["email"]], "skills": profile.get("skills", []), "degrees": profile.get("education", []), "languages": [], "years_of_experience": []}
    candidate = build_candidate_profile(extraction, target_role=(profile.get("preferred_roles") or [None])[0], preferred_country=profile.get("preferred_country"))
    jobs = [platform_job_to_matching_job(job) for job in store.jobs.values() if job.get("status") == "published"]
    return {"matches": rank_jobs(candidate, jobs, limit=20)}


@router.post("/jobs/{job_id}/candidates")
def job_candidate_matches(job_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    matching_job = platform_job_to_matching_job(job)
    matches = []
    for candidate_user_id, profile in store.candidate_profiles.items():
        user_record = store.users.get(candidate_user_id, {})
        extraction = {"name": [user_record.get("full_name", "")], "email_addresses": [user_record.get("email", "")], "skills": profile.get("skills", []), "degrees": profile.get("education", []), "languages": [], "years_of_experience": []}
        candidate = build_candidate_profile(extraction, target_role=job.get("category"), preferred_country=job.get("country"))
        match = rank_jobs(candidate, [matching_job], limit=1)[0]
        match["candidate_id"] = candidate_user_id
        match["candidate_name"] = user_record.get("full_name")
        matches.append(match)
    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return {"matches": matches}

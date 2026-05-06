from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas import CandidateProfileUpdate, RecruiterProfileUpdate
from ..security import require_role
from ..store import save_platform_store, store


router = APIRouter(tags=["Profiles"])


@router.get("/candidates/me/profile")
def get_candidate_profile(user: dict = Depends(require_role("candidate"))):
    return {"profile": store.candidate_profiles.get(user["id"], {})}


@router.patch("/candidates/me/profile")
def update_candidate_profile(payload: CandidateProfileUpdate, user: dict = Depends(require_role("candidate"))):
    profile = store.candidate_profiles.setdefault(user["id"], {"user_id": user["id"]})
    profile.update(payload.model_dump())
    store.audit(user["id"], "update_candidate_profile", "candidate_profile", user["id"])
    save_platform_store()
    return {"profile": profile}


@router.get("/recruiters/me/profile")
def get_recruiter_profile(user: dict = Depends(require_role("recruiter"))):
    return {"profile": store.recruiter_profiles.get(user["id"], {})}


@router.patch("/recruiters/me/profile")
def update_recruiter_profile(payload: RecruiterProfileUpdate, user: dict = Depends(require_role("recruiter"))):
    profile = store.recruiter_profiles.setdefault(user["id"], {"user_id": user["id"]})
    profile.update(payload.model_dump(exclude_unset=True))
    store.audit(user["id"], "update_recruiter_profile", "recruiter_profile", user["id"])
    save_platform_store()
    return {"profile": profile}


@router.get("/candidates/me/dashboard")
def candidate_dashboard(user: dict = Depends(require_role("candidate"))):
    applications = [item for item in store.applications.values() if item["candidate_id"] == user["id"]]
    notifications = [item for item in store.notifications.values() if item["user_id"] == user["id"] and not item.get("read")]
    profile = store.candidate_profiles.get(user["id"], {})
    available_jobs = [job for job in store.jobs.values() if job.get("status") == "published"]
    return {
        "available_jobs": len(available_jobs),
        "recommended_jobs": len(available_jobs),
        "best_match_score": 91,
        "applications_count": len(applications),
        "cv_quality_score": profile.get("cv_quality_score", 0),
        "unread_notifications": len(notifications),
        "profile": profile,
    }


@router.get("/recruiters/me/dashboard")
def recruiter_dashboard(user: dict = Depends(require_role("recruiter"))):
    profile = store.recruiter_profiles.get(user["id"], {})
    company_id = profile.get("company_id")
    jobs = [item for item in store.jobs.values() if item.get("company_id") == company_id]
    applications = [item for item in store.applications.values() if item.get("job_id") in {job["id"] for job in jobs}]
    shortlisted = [item for item in store.shortlists.values() if item.get("job_id") in {job["id"] for job in jobs}]
    ai_pending = [item for item in store.ai_jobs.values() if item.get("status") in {"queued", "running", "retrying"}]
    return {
        "active_jobs": len([job for job in jobs if job.get("status") == "published"]),
        "applications_count": len(applications),
        "shortlisted_candidates": len(shortlisted),
        "average_matching_score": 78,
        "best_candidate_recommendations": len(store.candidate_profiles),
        "pending_cv_processing": len(ai_pending),
        "profile": profile,
    }

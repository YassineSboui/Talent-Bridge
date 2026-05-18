from __future__ import annotations

from fastapi import APIRouter, Depends

from ..security import require_role
from ..store import store


router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("")
def search_candidates(skill: str | None = None, location: str | None = None, min_quality: int | None = None, user: dict = Depends(require_role("recruiter", "admin"))):
    candidates = []
    for user_id, profile in store.candidate_profiles.items():
        user_record = store.users.get(user_id, {})
        item = {"candidate_id": user_id, "name": user_record.get("full_name"), "email": user_record.get("email"), **profile}
        candidates.append(item)
    if skill:
        skill_lower = skill.lower()
        candidates = [item for item in candidates if any(skill_lower in s.lower() for s in item.get("skills", []))]
    if location:
        candidates = [item for item in candidates if location.lower() in (item.get("location") or "").lower()]
    if min_quality is not None:
        candidates = [item for item in candidates if (item.get("cv_quality_score") or 0) >= min_quality]
    return {"candidates": candidates}


@router.get("/{candidate_id}")
def candidate_details(candidate_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    user_record = store.users.get(candidate_id, {})
    profile = store.candidate_profiles.get(candidate_id, {})
    cvs = [cv for cv in store.cv_documents.values() if cv.get("owner_id") == candidate_id]
    applications = [app for app in store.applications.values() if app.get("candidate_id") == candidate_id]
    return {"candidate": {"candidate_id": candidate_id, "name": user_record.get("full_name"), "email": user_record.get("email"), **profile}, "cvs": cvs, "applications": applications}

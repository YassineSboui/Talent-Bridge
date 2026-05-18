from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import now_iso
from ..security import require_role
from ..store import save_platform_store, store


router = APIRouter(tags=["Shortlists"])


@router.get("/jobs/{job_id}/shortlist")
def get_shortlist(job_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    return {"shortlist": [item for item in store.shortlists.values() if item["job_id"] == job_id]}


@router.post("/jobs/{job_id}/shortlist/{candidate_id}")
def add_to_shortlist(job_id: int, candidate_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    if job_id not in store.jobs or candidate_id not in store.users:
        raise HTTPException(status_code=404, detail="Job or candidate not found")
    shortlist_id = store.next_id("shortlist")
    item = {"id": shortlist_id, "job_id": job_id, "candidate_id": candidate_id, "created_by": user["id"], "created_at": now_iso()}
    store.shortlists[shortlist_id] = item
    for application in store.applications.values():
        if application["job_id"] == job_id and application["candidate_id"] == candidate_id:
            application["status"] = "shortlisted"
            application["timeline"].append({"status": "shortlisted", "at": now_iso(), "by": user["id"], "note": "Added to shortlist"})
    store.audit(user["id"], "shortlist_candidate", "shortlist", shortlist_id)
    save_platform_store()
    return {"shortlist_item": item}


@router.delete("/jobs/{job_id}/shortlist/{candidate_id}")
def remove_from_shortlist(job_id: int, candidate_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    to_delete = [key for key, item in store.shortlists.items() if item["job_id"] == job_id and item["candidate_id"] == candidate_id]
    for key in to_delete:
        del store.shortlists[key]
    store.audit(user["id"], "remove_shortlist_candidate", "job", job_id, {"candidate_id": candidate_id})
    save_platform_store()
    return {"removed": len(to_delete)}

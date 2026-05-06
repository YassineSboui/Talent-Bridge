from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..security import require_role
from ..store import reset_platform_demo_data, save_platform_store, store


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def admin_dashboard(user: dict = Depends(require_role("admin"))):
    candidates = [item for item in store.users.values() if item.get("role") == "candidate"]
    recruiters = [item for item in store.users.values() if item.get("role") == "recruiter"]
    succeeded_ai = [job for job in store.ai_jobs.values() if job.get("status") == "succeeded"]
    failed_ai = [job for job in store.ai_jobs.values() if job.get("status") == "failed"]
    return {
        "users": len(store.users),
        "candidates": len(candidates),
        "recruiters": len(recruiters),
        "companies": len(store.companies),
        "jobs": len(store.jobs),
        "cvs_processed": len([cv for cv in store.cv_documents.values() if cv.get("quality")]),
        "applications": len(store.applications),
        "ai_jobs": len(store.ai_jobs),
        "failed_ai_jobs": len(failed_ai),
        "average_processing_ms": round(sum(job.get("duration_ms", 0) for job in succeeded_ai) / max(len(succeeded_ai), 1), 2),
        "recent_activity": list(store.audit_logs.values())[-8:],
    }


@router.get("/users")
def admin_users(user: dict = Depends(require_role("admin"))):
    return {"users": [{key: value for key, value in item.items() if key != "password_hash"} for item in store.users.values()]}


@router.get("/companies")
def admin_companies(user: dict = Depends(require_role("admin"))):
    return {"companies": list(store.companies.values())}


@router.get("/jobs")
def admin_jobs(user: dict = Depends(require_role("admin"))):
    return {"jobs": list(store.jobs.values())}


@router.get("/ai-jobs")
def admin_ai_jobs(status: str | None = None, user: dict = Depends(require_role("admin"))):
    jobs = list(store.ai_jobs.values())
    if status:
        jobs = [job for job in jobs if job.get("status") == status]
    return {"ai_jobs": jobs}


@router.post("/ai-jobs/{ai_job_id}/retry")
def retry_ai_job(ai_job_id: int, user: dict = Depends(require_role("admin"))):
    job = store.ai_jobs.get(ai_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="AI job not found")
    job["status"] = "retrying"
    store.audit(user["id"], "retry_ai_job", "ai_job", ai_job_id)
    save_platform_store()
    return {"ai_job": job}


@router.get("/audit-logs")
def audit_logs(user: dict = Depends(require_role("admin"))):
    return {"audit_logs": list(store.audit_logs.values())}


@router.post("/reset-demo-data")
def reset_demo_data(user: dict = Depends(require_role("admin"))):
    reset_platform_demo_data()
    return {"status": "reset", "message": "Demo data reset. Demo accounts and seed jobs were recreated."}

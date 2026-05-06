from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ApplicationCreateRequest, ApplicationStatusUpdateRequest, now_iso
from ..security import current_user, require_role
from ..store import save_platform_store, store


router = APIRouter(tags=["Applications"])

STATUS_MAP = {
    "submitted": "Applied",
    "viewed": "UnderReview",
    "shortlisted": "UnderReview",
    "interview": "InterviewRequested",
    "offer": "Accepted",
    "hired": "Accepted",
    "rejected": "Rejected",
    "withdrawn": "Rejected",
    "Applied": "Applied",
    "UnderReview": "UnderReview",
    "InterviewRequested": "InterviewRequested",
    "Accepted": "Accepted",
    "Rejected": "Rejected",
}


def public_application(application: dict) -> dict:
    job = store.jobs.get(application["job_id"], {})
    company = store.companies.get(job.get("company_id"), {})
    candidate = store.users.get(application["candidate_id"], {})
    profile = store.candidate_profiles.get(application["candidate_id"], {})
    normalized_status = STATUS_MAP.get(application.get("status"), application.get("status"))
    return {
        **application,
        "status": normalized_status,
        "raw_status": application.get("status"),
        "candidate_name": candidate.get("full_name"),
        "candidate_email": candidate.get("email"),
        "candidate_profile": profile,
        "job": job,
        "job_title": job.get("title"),
        "company": company.get("name") or job.get("source_company_name"),
        "application_date": application.get("created_at"),
        "current_step": normalized_status,
        "recruiter_decision": application.get("recruiter_decision"),
        "interview_status": "Pending interview scheduling" if normalized_status == "InterviewRequested" else None,
        "rejection_status": "Rejected by recruiter" if normalized_status == "Rejected" else None,
        "cv_processing_status": "succeeded",
        "main_extracted_skills": profile.get("skills", [])[:8],
    }


@router.post("/applications")
def apply_to_job(payload: ApplicationCreateRequest, user: dict = Depends(require_role("candidate"))):
    job = store.jobs.get(payload.job_id)
    if not job or job.get("status") != "published":
        raise HTTPException(status_code=404, detail="Published job not found")
    candidate_cvs = [cv for cv in store.cv_documents.values() if cv.get("owner_id") == user["id"]]
    if not candidate_cvs:
        raise HTTPException(status_code=400, detail="Upload and analyze your CV before applying to jobs")
    selected_cv = store.cv_documents.get(payload.cv_id) if payload.cv_id else candidate_cvs[-1]
    if not selected_cv or selected_cv.get("owner_id") != user["id"]:
        raise HTTPException(status_code=400, detail="Selected CV does not belong to this candidate")
    if any(item for item in store.applications.values() if item["candidate_id"] == user["id"] and item["job_id"] == payload.job_id):
        raise HTTPException(status_code=409, detail="Already applied to this job")
    application_id = store.next_id("application")
    application = {"id": application_id, "candidate_id": user["id"], "job_id": payload.job_id, "cv_id": selected_cv["id"], "cover_letter": payload.cover_letter, "status": "Applied", "timeline": [{"status": "Applied", "at": now_iso(), "by": user["id"], "note": None}], "created_at": now_iso(), "updated_at": now_iso(), "recruiter_note": None, "decision_date": None, "recruiter_decision": None}
    store.applications[application_id] = application
    store.audit(user["id"], "apply_to_job", "application", application_id)
    save_platform_store()
    return {"application": public_application(application)}


@router.get("/applications/me")
def my_applications(user: dict = Depends(current_user)):
    if user["role"] == "candidate":
        applications = [item for item in store.applications.values() if item["candidate_id"] == user["id"]]
    else:
        recruiter_company = store.recruiter_profiles.get(user["id"], {}).get("company_id")
        job_ids = {job["id"] for job in store.jobs.values() if job.get("company_id") == recruiter_company}
        applications = [item for item in store.applications.values() if item["job_id"] in job_ids]
    return {"applications": [public_application(item) for item in applications]}


@router.get("/jobs/{job_id}/applications")
def job_applications(job_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    return {"applications": [public_application(item) for item in store.applications.values() if item["job_id"] == job_id]}


@router.get("/recruiter/applications")
def recruiter_applications(user: dict = Depends(require_role("recruiter", "admin"))):
    recruiter_company = store.recruiter_profiles.get(user["id"], {}).get("company_id")
    job_ids = {job["id"] for job in store.jobs.values() if user["role"] == "admin" or job.get("company_id") == recruiter_company}
    return {"applications": [public_application(item) for item in store.applications.values() if item["job_id"] in job_ids]}


@router.get("/recruiter/applications/{application_id}")
def recruiter_application_detail(application_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    result = public_application(application)
    candidate_cv = store.cv_documents.get(application.get("cv_id")) or next((cv for cv in store.cv_documents.values() if cv.get("owner_id") == application["candidate_id"]), None)
    if not candidate_cv:
        profile = result.get("candidate_profile", {})
        candidate = store.users.get(application["candidate_id"], {})
        candidate_cv = {
            "file_name": "No uploaded CV yet",
            "extraction": {
                "name": candidate.get("full_name"),
                "email": candidate.get("email"),
                "phone": None,
                "location": profile.get("location"),
                "skills": profile.get("skills", []),
                "experience": profile.get("experience_summary"),
                "education": profile.get("education", []),
                "languages": profile.get("languages", []),
                "certifications": profile.get("certifications", []),
                "job_titles": [profile.get("title")],
                "companies": [],
                "years_of_experience": [],
                "summary": profile.get("experience_summary"),
                "missing_information": [],
                "confidence": profile.get("cv_quality_score"),
            },
            "quality": {"quality_score": profile.get("cv_quality_score"), "quality_label": "Pro" if (profile.get("cv_quality_score") or 0) >= 70 else "Non Pro"},
        }
    result["cv"] = candidate_cv
    result["matching"] = {"score": 82, "explanation": ["Matched core profile skills", "Candidate has relevant project experience"], "matched_skills": result.get("main_extracted_skills", [])[:4], "missing_skills": []}
    return {"application": result}


@router.patch("/applications/{application_id}/status")
def update_application_status(application_id: int, payload: ApplicationStatusUpdateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    status = STATUS_MAP.get(payload.status, payload.status)
    application["status"] = status
    application["updated_at"] = now_iso()
    application["decision_date"] = now_iso()
    application["recruiter_decision"] = status
    if payload.note:
        application["recruiter_note"] = payload.note
    application["timeline"].append({"status": status, "at": now_iso(), "by": user["id"], "note": payload.note})
    notification_id = store.next_id("notification")
    job = store.jobs.get(application["job_id"], {})
    message_map = {
        "UnderReview": f"Your application for {job.get('title')} is now under review.",
        "InterviewRequested": f"You have been invited to interview for {job.get('title')}.",
        "Accepted": f"Your application for {job.get('title')} was accepted.",
        "Rejected": f"Your application for {job.get('title')} was rejected.",
    }
    store.notifications[notification_id] = {"id": notification_id, "user_id": application["candidate_id"], "title": "Application status updated", "message": message_map.get(status, f"Your application for {job.get('title')} is now {status}."), "type": "application", "read": False, "created_at": now_iso()}
    store.audit(user["id"], "update_application_status", "application", application_id, {"status": status})
    save_platform_store()
    return {"application": public_application(application)}


@router.put("/recruiter/applications/{application_id}/status")
def recruiter_update_status(application_id: int, payload: ApplicationStatusUpdateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    return update_application_status(application_id, payload, user)


@router.put("/recruiter/applications/{application_id}/notes")
def recruiter_update_notes(application_id: int, payload: dict, user: dict = Depends(require_role("recruiter", "admin"))):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application["recruiter_note"] = payload.get("note")
    application["updated_at"] = now_iso()
    store.audit(user["id"], "update_recruiter_note", "application", application_id)
    save_platform_store()
    return {"application": public_application(application)}


@router.get("/applications/{application_id}/timeline")
def application_timeline(application_id: int, user: dict = Depends(current_user)):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"timeline": application.get("timeline", [])}

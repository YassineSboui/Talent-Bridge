from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ApplicationCreateRequest, ApplicationStatusUpdateRequest, InterviewSlotDeclineRequest, InterviewSlotProposalRequest, InterviewSlotSelectionRequest, now_iso
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
    "InterviewScheduling": "InterviewScheduling",
    "InterviewTimeProposed": "InterviewTimeProposed",
    "InterviewTimeConfirmed": "InterviewRequested",
    "InterviewSlotsDeclined": "InterviewSlotsDeclined",
    "Accepted": "Accepted",
    "Rejected": "Rejected",
}


def parse_future_slot(value: str) -> str:
    try:
        normalized = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid interview slot datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed_utc = parsed.astimezone(timezone.utc)
    if parsed_utc <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Interview slots must be in the future")
    return parsed_utc.isoformat().replace("+00:00", "Z")


def human_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return value
    return parsed.strftime("%d/%m/%Y at %H:%M UTC")


def notify_user(user_id: int, title: str, message: str, notification_type: str = "application") -> None:
    notification_id = store.next_id("notification")
    store.notifications[notification_id] = {"id": notification_id, "user_id": user_id, "title": title, "message": message, "type": notification_type, "read": False, "created_at": now_iso()}


def application_recruiter_id(application: dict) -> int | None:
    job = store.jobs.get(application.get("job_id"), {})
    created_by = job.get("created_by")
    if created_by:
        return created_by
    company_id = job.get("company_id")
    for recruiter_id, profile in store.recruiter_profiles.items():
        if profile.get("company_id") == company_id:
            return recruiter_id
    return None


def ensure_recruiter_can_manage_application(application: dict, user: dict) -> None:
    if user.get("role") == "admin":
        return
    recruiter_company = store.recruiter_profiles.get(user["id"], {}).get("company_id")
    job = store.jobs.get(application.get("job_id"), {})
    if not recruiter_company or job.get("company_id") != recruiter_company:
        raise HTTPException(status_code=403, detail="This application does not belong to your company")


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
        "interview_status": application.get("interview_status") or ("Pending interview scheduling" if normalized_status == "InterviewRequested" else None),
        "interview_slots": application.get("interview_slots", []),
        "selected_interview_slot": application.get("selected_interview_slot"),
        "interview_decline_reason": application.get("interview_decline_reason"),
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
    if selected_cv.get("document_check", {}).get("is_cv") is False:
        raise HTTPException(status_code=422, detail="This file does not look like a real CV. Please upload a real CV PDF before applying.")
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
    ensure_recruiter_can_manage_application(application, user)
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
    ensure_recruiter_can_manage_application(application, user)
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
        "InterviewRequested": f"You have been invited to interview for {job.get('title')}. The recruiter will propose interview times.",
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
    ensure_recruiter_can_manage_application(application, user)
    application["recruiter_note"] = payload.get("note")
    application["updated_at"] = now_iso()
    store.audit(user["id"], "update_recruiter_note", "application", application_id)
    save_platform_store()
    return {"application": public_application(application)}


@router.post("/recruiter/applications/{application_id}/interview-slots")
def propose_interview_slots(application_id: int, payload: InterviewSlotProposalRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    ensure_recruiter_can_manage_application(application, user)
    normalized_slots = []
    seen = set()
    for value in payload.slots:
        slot_start = parse_future_slot(value)
        if slot_start in seen:
            continue
        seen.add(slot_start)
        normalized_slots.append({"id": f"slot-{len(normalized_slots) + 1}", "start_at": slot_start, "status": "proposed"})
    if not normalized_slots:
        raise HTTPException(status_code=422, detail="At least one future interview slot is required")
    application["interview_slots"] = normalized_slots
    application["selected_interview_slot"] = None
    application["interview_decline_reason"] = None
    application["interview_status"] = "Waiting for candidate to choose an interview time"
    application["status"] = "InterviewTimeProposed"
    application["recruiter_decision"] = "InterviewTimeProposed"
    application["updated_at"] = now_iso()
    if payload.note:
        application["recruiter_note"] = payload.note
    application.setdefault("timeline", []).append({"status": "InterviewTimeProposed", "at": now_iso(), "by": user["id"], "note": payload.note or f"Proposed {len(normalized_slots)} interview slots"})
    job = store.jobs.get(application["job_id"], {})
    notify_user(application["candidate_id"], "Interview slots proposed", f"You have been selected for {job.get('title')}. Please choose the interview time that fits you best.")
    store.audit(user["id"], "propose_interview_slots", "application", application_id, {"slots": normalized_slots})
    save_platform_store()
    return {"application": public_application(application)}


@router.post("/applications/{application_id}/interview-slots/select")
def select_interview_slot(application_id: int, payload: InterviewSlotSelectionRequest, user: dict = Depends(require_role("candidate"))):
    application = store.applications.get(application_id)
    if not application or application.get("candidate_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Application not found")
    slots = application.get("interview_slots") or []
    selected = next((slot for slot in slots if slot.get("id") == payload.slot_id and slot.get("status") == "proposed"), None)
    if not selected:
        raise HTTPException(status_code=422, detail="Please select one of the proposed interview slots")
    for slot in slots:
        slot["status"] = "confirmed" if slot.get("id") == payload.slot_id else "not_selected"
    application["selected_interview_slot"] = selected
    application["interview_status"] = "Interview time confirmed"
    application["status"] = "InterviewRequested"
    application["recruiter_decision"] = "InterviewRequested"
    application["updated_at"] = now_iso()
    confirmed_label = human_datetime(selected.get("start_at"))
    application.setdefault("timeline", []).append({"status": "InterviewRequested", "at": now_iso(), "by": user["id"], "note": f"Candidate confirmed {confirmed_label}"})
    job = store.jobs.get(application["job_id"], {})
    recruiter_id = application_recruiter_id(application)
    if recruiter_id:
        notify_user(recruiter_id, "Interview time confirmed", f"{user.get('full_name')} confirmed an interview time for {job.get('title')}: {confirmed_label}.")
    notify_user(user["id"], "Interview confirmed", f"Your interview for {job.get('title')} is confirmed for {confirmed_label}.")
    store.audit(user["id"], "select_interview_slot", "application", application_id, {"slot": selected})
    save_platform_store()
    return {"application": public_application(application)}


@router.post("/applications/{application_id}/interview-slots/decline")
def decline_interview_slots(application_id: int, payload: InterviewSlotDeclineRequest, user: dict = Depends(require_role("candidate"))):
    application = store.applications.get(application_id)
    if not application or application.get("candidate_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Application not found")
    if not application.get("interview_slots"):
        raise HTTPException(status_code=422, detail="No interview slots are available to decline")
    for slot in application["interview_slots"]:
        if slot.get("status") == "proposed":
            slot["status"] = "declined"
    reason = payload.reason or "The proposed times do not fit the candidate."
    application["selected_interview_slot"] = None
    application["interview_decline_reason"] = reason
    application["interview_status"] = "Candidate asked for new interview times"
    application["status"] = "InterviewSlotsDeclined"
    application["recruiter_decision"] = "InterviewSlotsDeclined"
    application["updated_at"] = now_iso()
    application.setdefault("timeline", []).append({"status": "InterviewSlotsDeclined", "at": now_iso(), "by": user["id"], "note": reason})
    job = store.jobs.get(application["job_id"], {})
    recruiter_id = application_recruiter_id(application)
    if recruiter_id:
        notify_user(recruiter_id, "New interview times needed", f"{user.get('full_name')} declined all proposed times for {job.get('title')}. Reason: {reason}")
    notify_user(user["id"], "Interview times declined", f"The recruiter has been notified to propose new interview times for {job.get('title')}.")
    store.audit(user["id"], "decline_interview_slots", "application", application_id, {"reason": reason})
    save_platform_store()
    return {"application": public_application(application)}


@router.get("/applications/{application_id}/timeline")
def application_timeline(application_id: int, user: dict = Depends(current_user)):
    application = store.applications.get(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"timeline": application.get("timeline", [])}

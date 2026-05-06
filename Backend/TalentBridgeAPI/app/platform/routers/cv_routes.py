from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
import base64

from DocumentAI.CVQualityScoring.src.quality import classify_cv_quality
from NLP.CVExtraction.src.pdf_reader import extract_text_from_pdf

from ..schemas import now_iso
from ..security import require_role
from ..store import save_platform_store, store


router = APIRouter(prefix="/cv", tags=["CV"])


@router.get("/my")
def my_cvs(user: dict = Depends(require_role("candidate", "recruiter", "admin"))):
    return {"cvs": [cv for cv in store.cv_documents.values() if cv.get("owner_id") == user["id"]]}


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), user: dict = Depends(require_role("candidate", "recruiter", "admin"))):
    content = await file.read()
    cv_id = store.next_id("cv")
    ai_job_id = store.next_id("ai_job")
    store.ai_jobs[ai_job_id] = {"id": ai_job_id, "type": "cv_extraction", "status": "running", "user_id": user["id"], "cv_id": cv_id, "created_at": now_iso(), "error": None}
    try:
        text = extract_text_from_pdf(content)
        from ...main import run_full_cv_extraction
        full_extraction = run_full_cv_extraction(text, include_raw_text=True)
        extraction_data = full_extraction.model_dump() if hasattr(full_extraction, "model_dump") else full_extraction.dict()
        quality = classify_cv_quality(text, extraction_data)
        extraction = {
            "raw_text_preview": text[:1600],
            "text_length": len(text),
            "name": extraction_data.get("name", []),
            "email_addresses": extraction_data.get("email_addresses", []),
            "phone": None,
            "location": None,
            "detected_skills": extraction_data.get("skills", []),
            "skills": extraction_data.get("skills", []),
            "companies": extraction_data.get("companies", []),
            "colleges": extraction_data.get("colleges", []),
            "degrees": extraction_data.get("degrees", []),
            "years_of_experience": extraction_data.get("years_of_experience", []),
            "experience": ", ".join(extraction_data.get("years_of_experience", [])) or ("Detected timeline/date signals" if quality["features"].get("has_professional_dates") else "No clear timeline detected"),
            "education": extraction_data.get("degrees", []) or extraction_data.get("colleges", []) or ("Education section detected" if quality["features"].get("has_education_section") else "Education section missing"),
            "languages": extraction_data.get("languages", []) or ("Languages section detected" if quality["features"].get("has_languages_section") else "No language section detected"),
            "certifications": "Certification section detected" if quality["features"].get("has_certifications_section") else "No certification section detected",
            "linkedin": extraction_data.get("linkedin"),
            "github": extraction_data.get("github"),
            "detected_language": extraction_data.get("detected_language"),
            "missing_information": quality.get("issues", []),
            "suggested_improvements": quality.get("suggestions", []),
            "full_ner_result": {key: value for key, value in extraction_data.items() if key != "raw_text"},
        }
        store.cv_documents[cv_id] = {"id": cv_id, "owner_id": user["id"], "file_name": file.filename, "content_type": file.content_type or "application/pdf", "preview_data_url": f"data:{file.content_type or 'application/pdf'};base64,{base64.b64encode(content).decode('ascii')}", "uploaded_at": now_iso(), "extraction": extraction, "quality": quality}
        store.ai_jobs[ai_job_id]["status"] = "succeeded"
        store.audit(user["id"], "upload_cv", "cv", cv_id)
        save_platform_store()
        return {"cv": store.cv_documents[cv_id], "ai_job": store.ai_jobs[ai_job_id]}
    except Exception as exc:
        store.ai_jobs[ai_job_id]["status"] = "failed"
        store.ai_jobs[ai_job_id]["error"] = str(exc)
        save_platform_store()
        raise


@router.get("/{cv_id}")
def get_cv(cv_id: int, user: dict = Depends(require_role("candidate", "recruiter", "admin"))):
    return {"cv": store.cv_documents.get(cv_id)}


@router.get("/{cv_id}/extraction")
def get_cv_extraction(cv_id: int, user: dict = Depends(require_role("candidate", "recruiter", "admin"))):
    cv = store.cv_documents.get(cv_id) or {}
    return {"extraction": cv.get("extraction")}


@router.get("/{cv_id}/quality")
def get_cv_quality(cv_id: int, user: dict = Depends(require_role("candidate", "recruiter", "admin"))):
    cv = store.cv_documents.get(cv_id) or {}
    return {"quality": cv.get("quality")}

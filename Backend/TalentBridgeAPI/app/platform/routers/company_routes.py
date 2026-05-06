from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import CompanyCreateRequest, CompanyUpdateRequest, now_iso
from ..security import require_role
from ..store import save_platform_store, store


router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("")
def create_company(payload: CompanyCreateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    company_id = store.next_id("company")
    company = {"id": company_id, **payload.model_dump(), "created_at": now_iso(), "created_by": user["id"]}
    store.companies[company_id] = company
    if user["role"] == "recruiter":
        store.recruiter_profiles.setdefault(user["id"], {"user_id": user["id"]})["company_id"] = company_id
    store.audit(user["id"], "create_company", "company", company_id)
    save_platform_store()
    return {"company": company}


@router.get("/{company_id}")
def get_company(company_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    company = store.companies.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"company": company}


@router.patch("/{company_id}")
def update_company(company_id: int, payload: CompanyUpdateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    company = store.companies.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.update(payload.model_dump(exclude_unset=True))
    store.audit(user["id"], "update_company", "company", company_id)
    save_platform_store()
    return {"company": company}

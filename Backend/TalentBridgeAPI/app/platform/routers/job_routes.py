from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import JobCreateRequest, JobUpdateRequest, now_iso
from ..security import current_user, require_role
from ..store import save_platform_store, store


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
def list_jobs(
    q: str | None = None,
    keyword: str | None = None,
    location: str | None = None,
    contract_type: str | None = None,
    experience_level: str | None = None,
    remote: bool | None = None,
    work_mode: str | None = None,
    skill: str | None = None,
    skills: str | None = None,
    min_salary: float | None = None,
    salaryMin: float | None = None,
    salaryMax: float | None = None,
    classification: str | None = None,
    segment: str | None = None,
    segmentation: str | None = None,
    page: int = 1,
    page_size: int = 20,
    pageSize: int | None = None,
    user: dict = Depends(current_user),
):
    if user["role"] == "candidate":
        warehouse_result = list_warehouse_jobs(
            keyword=keyword or q,
            location=location,
            contract_type=contract_type,
            experience_level=experience_level,
            remote=remote,
            work_mode=work_mode,
            skill=skill or skills,
            salary_min=salaryMin if salaryMin is not None else min_salary,
            salary_max=salaryMax,
            classification=classification,
            segmentation=segmentation or segment,
            page=page,
            page_size=pageSize or page_size,
            user=user,
        )
        if warehouse_result is not None:
            return warehouse_result

    jobs = list(store.jobs.values())
    if user["role"] == "candidate":
        jobs = [job for job in jobs if job.get("status") == "published"]
    keyword = keyword or q
    if keyword:
        query = keyword.lower()
        jobs = [job for job in jobs if query in job.get("title", "").lower() or query in job.get("category", "").lower() or query in job.get("description", "").lower()]
    if location:
        loc = location.lower()
        jobs = [job for job in jobs if loc in (job.get("country") or "").lower() or loc in (job.get("city") or "").lower()]
    if contract_type:
        jobs = [job for job in jobs if contract_type.lower() in (job.get("schedule_type") or "").lower()]
    if experience_level:
        jobs = [job for job in jobs if job.get("experience_level") == experience_level]
    if remote is not None:
        jobs = [job for job in jobs if bool(job.get("remote")) == remote]
    if work_mode:
        jobs = [job for job in jobs if work_mode.lower() in (job.get("work_mode") or "").lower()]
    skill_value = skill or skills
    if skill_value:
        skill_lower = skill_value.lower()
        jobs = [job for job in jobs if any(skill_lower in item.lower() for item in job.get("required_skills", []))]
    salary_min = salaryMin if salaryMin is not None else min_salary
    if salary_min is not None:
        jobs = [job for job in jobs if (job.get("salary_year_avg") or 0) >= salary_min]
    if salaryMax is not None:
        jobs = [job for job in jobs if (job.get("salary_year_avg") or 0) <= salaryMax]
    if classification:
        jobs = [job for job in jobs if classification.lower() in (job.get("classification", {}).get("remote_class") or "").lower() or classification.lower() in (job.get("classification", {}).get("schedule_class") or "").lower()]
    segment_value = segmentation or segment
    if segment_value:
        jobs = [job for job in jobs if segment_value.lower() in (job.get("segmentation", {}).get("segment_name") or "").lower()]
    total = len(jobs)
    page = max(1, page)
    page_size = pageSize or page_size
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size
    items = jobs[start:start + page_size]
    applied_job_ids = {item["job_id"] for item in store.applications.values() if item.get("candidate_id") == user.get("id")}
    for job in items:
        job["application_status"] = "Applied" if job["id"] in applied_job_ids else None
        job["has_applied"] = job["id"] in applied_job_ids
    return {
        "items": items,
        "jobs": items,
        "totalCount": total,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "page_size": page_size,
        "hasNextPage": start + page_size < total,
    }


def list_warehouse_jobs(
    keyword: str | None,
    location: str | None,
    contract_type: str | None,
    experience_level: str | None,
    remote: bool | None,
    work_mode: str | None,
    skill: str | None,
    salary_min: float | None,
    salary_max: float | None,
    classification: str | None,
    segmentation: str | None,
    page: int,
    page_size: int,
    user: dict,
) -> dict | None:
    try:
        import pyodbc
    except Exception:
        return None

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    clauses = ["job_title IS NOT NULL"]
    params = []

    if keyword:
        clauses.append("(job_title LIKE ? OR category_name LIKE ? OR company_name LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like, like])
    if location:
        clauses.append("(country LIKE ? OR city LIKE ?)")
        like = f"%{location}%"
        params.extend([like, like])
    if contract_type:
        clauses.append("schedule_types_csv LIKE ?")
        params.append(f"%{contract_type}%")
    if skill:
        clauses.append("skills_csv LIKE ?")
        params.append(f"%{skill}%")
    if remote is not None:
        clauses.append("is_work_from_home = ?")
        params.append(1 if remote else 0)
    if work_mode:
        mode = work_mode.lower()
        if mode == "remote":
            clauses.append("is_work_from_home = 1")
        elif mode in {"onsite", "hybrid"}:
            clauses.append("is_work_from_home = 0")
    if experience_level:
        if experience_level == "senior":
            clauses.append("job_title LIKE '%senior%'")
        elif experience_level == "junior":
            clauses.append("job_title LIKE '%junior%'")
    if salary_min and salary_min > 0:
        clauses.append("salary_year_avg >= ?")
        params.append(salary_min)
    if salary_max and salary_max < 220000:
        clauses.append("salary_year_avg <= ?")
        params.append(salary_max)
    if classification:
        clauses.append("(category_name LIKE ? OR schedule_types_csv LIKE ?)")
        like = f"%{classification}%"
        params.extend([like, like])
    if segmentation:
        clauses.append("skill_categories_csv LIKE ?")
        params.append(f"%{segmentation}%")

    where_sql = " AND ".join(clauses)
    offset = (page - 1) * page_size
    connection_string = os.getenv(
        "DW_DATAJOBS_CONNECTION_STRING",
        "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DW_DataJobs;Trusted_Connection=yes;TrustServerCertificate=yes;",
    )
    count_sql = f"SELECT COUNT(*) FROM dbo.vw_job_matching WHERE {where_sql};"
    data_sql = f"""
        SELECT
            job_posting_key, job_title, category_name, company_name, country, city,
            is_work_from_home, salary_year_avg, schedule_types_csv, skills_csv,
            skill_categories_csv, has_salary_info, posted_date
        FROM dbo.vw_job_matching
        WHERE {where_sql}
        ORDER BY has_salary_info DESC, posted_date DESC, job_posting_key DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
    """
    try:
        with pyodbc.connect(connection_string) as connection:
            cursor = connection.cursor()
            total = int(cursor.execute(count_sql, params).fetchone()[0])
            rows = cursor.execute(data_sql, [*params, offset, page_size]).fetchall()
    except Exception:
        return None

    items = [warehouse_row_to_platform_job(row, user) for row in rows]
    return {
        "items": items,
        "jobs": items,
        "totalCount": total,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "page_size": page_size,
        "hasNextPage": offset + page_size < total,
    }


def warehouse_row_to_platform_job(row, user: dict) -> dict:
    skills = [item.strip().lower() for item in str(row.skills_csv or "").split(",") if item.strip()][:10]
    if not skills:
        skills = ["sql", "python"] if "data" in str(row.category_name or "").lower() else ["communication"]
    salary = float(row.salary_year_avg) if row.salary_year_avg is not None else None
    job_id = int(row.job_posting_key)
    segment_name = clean_label(str(row.skill_categories_csv or row.category_name or "General IT"))
    job = {
        "id": job_id,
        "warehouse_source": True,
        "company_id": 1,
        "source_company_name": row.company_name,
        "title": str(row.job_title or "Untitled job"),
        "category": str(row.category_name or "IT Job"),
        "country": str(row.country or "Unknown"),
        "city": str(row.city or "Unknown"),
        "remote": bool(row.is_work_from_home),
        "work_mode": "remote" if bool(row.is_work_from_home) else "onsite/hybrid",
        "schedule_type": str(row.schedule_types_csv or "Unknown"),
        "experience_level": "senior" if "senior" in str(row.job_title or "").lower() else "junior" if "junior" in str(row.job_title or "").lower() else "mid",
        "description": f"Warehouse job imported from SQL for {row.category_name or 'IT'} roles. Required skills include {', '.join(skills[:5])}.",
        "required_skills": skills,
        "salary_year_avg": salary,
        "estimated_salary_range": [int(salary * 0.9), int(salary * 1.12)] if salary else None,
        "classification": {"remote_class": "remote" if bool(row.is_work_from_home) else "onsite/hybrid", "schedule_class": str(row.schedule_types_csv or "Unknown"), "confidence": 76},
        "segmentation": {"segment_name": segment_name, "cluster_id": job_id % 7, "confidence": 68},
        "status": "published",
        "created_at": str(row.posted_date) if row.posted_date else None,
    }
    store.jobs.setdefault(job_id, job)
    applied_job_ids = {item["job_id"] for item in store.applications.values() if item.get("candidate_id") == user.get("id")}
    job["application_status"] = "Applied" if job_id in applied_job_ids else None
    job["has_applied"] = job_id in applied_job_ids
    return job


def clean_label(value: str) -> str:
    parts = []
    seen = set()
    for item in value.replace(";", ",").split(","):
        label = item.strip()
        key = label.lower()
        if label and key not in seen:
            seen.add(key)
            parts.append(label)
    return ", ".join(parts[:3]) or "General IT"


@router.post("")
def create_job(payload: JobCreateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    if payload.company_id not in store.companies:
        raise HTTPException(status_code=404, detail="Company not found")
    job_id = store.next_id("job")
    job = {"id": job_id, **payload.model_dump(), "status": "draft", "created_by": user["id"], "created_at": now_iso()}
    store.jobs[job_id] = job
    store.audit(user["id"], "create_job", "job", job_id)
    save_platform_store()
    return {"job": job}


@router.get("/{job_id}")
def get_job(job_id: int, user: dict = Depends(current_user)):
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}


@router.patch("/{job_id}")
def update_job(job_id: int, payload: JobUpdateRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.update(payload.model_dump(exclude_unset=True))
    store.audit(user["id"], "update_job", "job", job_id)
    save_platform_store()
    return {"job": job}


@router.post("/{job_id}/publish")
def publish_job(job_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job["status"] = "published"
    store.audit(user["id"], "publish_job", "job", job_id)
    save_platform_store()
    return {"job": job}


@router.post("/{job_id}/close")
def close_job(job_id: int, user: dict = Depends(require_role("recruiter", "admin"))):
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job["status"] = "closed"
    store.audit(user["id"], "close_job", "job", job_id)
    save_platform_store()
    return {"job": job}

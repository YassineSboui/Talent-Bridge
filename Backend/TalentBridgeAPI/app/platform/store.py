from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from typing import Any

from .schemas import now_iso


PERSIST_PATH = os.getenv("TALENTBRIDGE_PLATFORM_STORE", str(__import__("pathlib").Path(__file__).resolve().parents[4] / "Artifacts" / "platform_store.json"))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class PlatformStore:
    users: dict[int, dict[str, Any]] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)
    candidate_profiles: dict[int, dict[str, Any]] = field(default_factory=dict)
    recruiter_profiles: dict[int, dict[str, Any]] = field(default_factory=dict)
    companies: dict[int, dict[str, Any]] = field(default_factory=dict)
    jobs: dict[int, dict[str, Any]] = field(default_factory=dict)
    cv_documents: dict[int, dict[str, Any]] = field(default_factory=dict)
    applications: dict[int, dict[str, Any]] = field(default_factory=dict)
    shortlists: dict[int, dict[str, Any]] = field(default_factory=dict)
    notifications: dict[int, dict[str, Any]] = field(default_factory=dict)
    audit_logs: dict[int, dict[str, Any]] = field(default_factory=dict)
    ai_jobs: dict[int, dict[str, Any]] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=lambda: {
        "user": 0, "company": 0, "job": 0, "cv": 0, "application": 0, "shortlist": 0, "notification": 0, "audit": 0, "ai_job": 0,
    })

    def next_id(self, name: str) -> int:
        self.counters[name] += 1
        return self.counters[name]

    def create_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        self.tokens[token] = user_id
        return token

    def audit(self, actor_id: int | None, action: str, entity_type: str, entity_id: int | None, details: dict[str, Any] | None = None) -> None:
        audit_id = self.next_id("audit")
        self.audit_logs[audit_id] = {
            "id": audit_id,
            "actor_id": actor_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "created_at": now_iso(),
        }
        save_platform_store()


store = PlatformStore()


def save_platform_store() -> None:
    path = __import__("pathlib").Path(PERSIST_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "users": store.users,
        "candidate_profiles": store.candidate_profiles,
        "recruiter_profiles": store.recruiter_profiles,
        "companies": store.companies,
        "jobs": store.jobs,
        "cv_documents": store.cv_documents,
        "applications": store.applications,
        "shortlists": store.shortlists,
        "notifications": store.notifications,
        "audit_logs": store.audit_logs,
        "ai_jobs": store.ai_jobs,
        "counters": store.counters,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_platform_store() -> bool:
    path = __import__("pathlib").Path(PERSIST_PATH)
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    for key in ["users", "candidate_profiles", "recruiter_profiles", "companies", "jobs", "cv_documents", "applications", "shortlists", "notifications", "audit_logs", "ai_jobs"]:
        setattr(store, key, {int(k): v for k, v in payload.get(key, {}).items()})
    store.counters.update(payload.get("counters", {}))
    return bool(store.users)


def seed_platform() -> None:
    if store.users or load_platform_store():
        return
    admin_id = store.next_id("user")
    store.users[admin_id] = {"id": admin_id, "email": "admin@talentbridge.local", "password_hash": hash_password("admin123"), "full_name": "Platform Admin", "role": "admin", "status": "active", "created_at": now_iso()}

    company_seed = [
        ("Neosoft Analytics", "Data & BI", "Paris", "https://neosoft.example", "BI, analytics, and data engineering consulting."),
        ("CloudNova Labs", "Cloud AI", "Berlin", "https://cloudnova.example", "Cloud-native AI and data platforms."),
        ("MedData Systems", "HealthTech", "Remote", "https://meddata.example", "Healthcare analytics and reporting products."),
    ]
    company_ids = []
    for name, industry, location, website, description in company_seed:
        company_id = store.next_id("company")
        company_ids.append(company_id)
        store.companies[company_id] = {"id": company_id, "name": name, "industry": industry, "location": location, "website": website, "description": description, "created_at": now_iso()}

    recruiter_id = store.next_id("user")
    store.users[recruiter_id] = {"id": recruiter_id, "email": "recruiter@talentbridge.local", "password_hash": hash_password("recruiter123"), "full_name": "Demo Recruiter", "role": "recruiter", "status": "active", "created_at": now_iso()}
    store.recruiter_profiles[recruiter_id] = {"user_id": recruiter_id, "title": "Senior Technical Recruiter", "phone": None, "company_id": company_ids[0]}

    candidate_id = store.next_id("user")
    store.users[candidate_id] = {"id": candidate_id, "email": "candidate@talentbridge.local", "password_hash": hash_password("candidate123"), "full_name": "Demo Candidate", "role": "candidate", "status": "active", "created_at": now_iso()}
    store.candidate_profiles[candidate_id] = {"user_id": candidate_id, "title": "Junior Data Analyst", "location": "Tunis", "preferred_roles": ["Data Analyst", "Business Analyst"], "preferred_country": "France", "skills": ["python", "sql", "power bi", "excel", "tableau"], "education": ["Computer Science Bachelor"], "experience_summary": "Built dashboards and SQL reports during internships.", "languages": ["French", "English", "Arabic"], "certifications": ["PL-300 in progress"], "visibility": True, "cv_quality_score": 88}

    candidate_seed = [
        ("Syrine Kaabi", "Data Scientist", "Tunis", ["python", "sql", "machine learning", "pandas", "scikit-learn", "tableau"], 92),
        ("Chaima Riahi", "Business Analyst", "Sfax", ["business analysis", "scrum", "jira", "sql", "power bi", "uml"], 86),
        ("Baha Salami", "Data Engineer", "Ariana", ["python", "sql", "spark", "airflow", "docker", "aws"], 90),
        ("Soulayma Ben Dahsen", "QA Analyst", "Tunis", ["sql", "oracle", "scrum", "istqb", "java", "selenium"], 78),
    ]
    for full_name, title, location, skills, quality in candidate_seed:
        user_id = store.next_id("user")
        email = full_name.lower().replace(" ", ".") + "@talentbridge.local"
        store.users[user_id] = {"id": user_id, "email": email, "password_hash": hash_password("candidate123"), "full_name": full_name, "role": "candidate", "status": "active", "created_at": now_iso()}
        store.candidate_profiles[user_id] = {"user_id": user_id, "title": title, "location": location, "preferred_roles": [title], "preferred_country": "France", "skills": skills, "education": ["Engineering degree"], "experience_summary": f"Profile oriented toward {title} roles.", "languages": ["French", "English"], "certifications": [], "visibility": True, "cv_quality_score": quality}

    job_seed = [
        (company_ids[0], "Data Analyst BI", "Data Analyst", "France", "Paris", True, "Full-time", ["python", "sql", "power bi", "excel"], 62000, "Build executive dashboards, clean SQL datasets, and analyze KPI trends.", "remote", "BI Analytics", 91),
        (company_ids[0], "Business Data Analyst", "Business Analyst", "France", "Lyon", False, "Full-time", ["sql", "power bi", "jira", "business analysis"], 58000, "Translate business needs into reporting and analytics specifications.", "onsite", "Business Intelligence", 84),
        (company_ids[1], "Junior Data Engineer", "Data Engineer", "Germany", "Berlin", True, "Full-time", ["python", "sql", "spark", "airflow", "docker"], 72000, "Develop data pipelines and cloud ingestion jobs for analytics platforms.", "hybrid", "Cloud Data", 76),
        (company_ids[1], "Machine Learning Engineer", "Machine Learning Engineer", "Germany", "Remote", True, "Contractor", ["python", "machine learning", "pytorch", "docker", "kubernetes"], 88000, "Deploy ML models and monitor inference services for production systems.", "remote", "AI Engineering", 69),
        (company_ids[2], "Healthcare Data Analyst", "Data Analyst", "United States", "Remote", True, "Full-time", ["sql", "tableau", "python", "statistics"], 82000, "Analyze healthcare operations data and produce compliance dashboards.", "remote", "Healthcare Analytics", 73),
        (company_ids[2], "Cloud BI Consultant", "Cloud Engineer", "United Kingdom", "London", False, "Full-time", ["azure", "power bi", "sql", "devops"], 76000, "Help customers migrate reporting workloads to secure cloud infrastructure.", "hybrid", "Cloud BI", 61),
        (company_ids[1], "Senior Data Scientist", "Data Scientist", "Canada", "Montreal", True, "Full-time", ["python", "sql", "machine learning", "statistics", "scikit-learn"], 105000, "Build predictive models and explain insights to stakeholders.", "remote", "Predictive Analytics", 67),
        (company_ids[0], "Frontend Analytics Engineer", "Software Engineer", "Netherlands", "Amsterdam", False, "Full-time", ["javascript", "react", "sql", "dashboarding"], 70000, "Build data-rich product interfaces for analytics users.", "onsite", "Product Engineering", 54),
    ]
    for company_id, title, category, country, city, remote, schedule, skills, salary, description, work_mode, segment, classification_score in job_seed:
        job_id = store.next_id("job")
        store.jobs[job_id] = {
            "id": job_id,
            "company_id": company_id,
            "title": title,
            "category": category,
            "country": country,
            "city": city,
            "remote": remote,
            "work_mode": work_mode,
            "schedule_type": schedule,
            "experience_level": "junior" if "Junior" in title else "senior" if "Senior" in title else "mid",
            "description": description,
            "required_skills": skills,
            "salary_year_avg": salary,
            "estimated_salary_range": [int(salary * 0.9), int(salary * 1.12)],
            "classification": {"remote_class": work_mode, "schedule_class": schedule, "confidence": classification_score},
            "segmentation": {"segment_name": segment, "cluster_id": job_id % 7, "confidence": max(52, classification_score - 8)},
            "status": "published",
            "created_by": recruiter_id,
            "created_at": now_iso(),
        }

    for index, user_id in enumerate(list(store.candidate_profiles.keys())[1:4], start=1):
        application_id = store.next_id("application")
        store.applications[application_id] = {"id": application_id, "candidate_id": user_id, "job_id": index, "cover_letter": None, "status": ["submitted", "shortlisted", "interview"][index - 1], "timeline": [{"status": "submitted", "at": now_iso(), "by": user_id, "note": None}], "created_at": now_iso(), "recruiter_notes": "Strong profile, review technical fit."}

    for title, status, entity in [("CV extraction", "succeeded", "cv"), ("Matching calculation", "succeeded", "match"), ("Salary estimation", "succeeded", "job"), ("Recommendation generation", "failed", "recommendation")]:
        ai_job_id = store.next_id("ai_job")
        store.ai_jobs[ai_job_id] = {"id": ai_job_id, "type": title, "status": status, "entity": entity, "duration_ms": 850 + ai_job_id * 140, "created_at": now_iso(), "error": None if status == "succeeded" else "Demo failed job for admin monitoring"}

    seed_jobs_from_warehouse(company_ids, recruiter_id)
    save_platform_store()


def reset_platform_demo_data() -> None:
    path = __import__("pathlib").Path(PERSIST_PATH)
    if path.exists():
        path.unlink()
    store.users.clear()
    store.tokens.clear()
    store.candidate_profiles.clear()
    store.recruiter_profiles.clear()
    store.companies.clear()
    store.jobs.clear()
    store.cv_documents.clear()
    store.applications.clear()
    store.shortlists.clear()
    store.notifications.clear()
    store.audit_logs.clear()
    store.ai_jobs.clear()
    store.counters = {"user": 0, "company": 0, "job": 0, "cv": 0, "application": 0, "shortlist": 0, "notification": 0, "audit": 0, "ai_job": 0}
    seed_platform()


def seed_jobs_from_warehouse(company_ids: list[int], recruiter_id: int, limit: int = 120) -> None:
    if os.getenv("TALENTBRIDGE_SEED_WAREHOUSE_JOBS", "1").lower() in {"0", "false", "no"}:
        return
    try:
        import pyodbc
    except Exception:
        return
    try:
        seed_timeout = int(os.getenv("TALENTBRIDGE_WAREHOUSE_SEED_TIMEOUT", "5"))
    except ValueError:
        seed_timeout = 5
    connection_string = os.getenv(
        "DW_DATAJOBS_CONNECTION_STRING",
        "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DW_DataJobs;Trusted_Connection=yes;TrustServerCertificate=yes;",
    )
    query = f"""
        SELECT TOP ({limit})
            job_title,
            category_name,
            company_name,
            country,
            city,
            is_work_from_home,
            salary_year_avg,
            schedule_types_csv,
            skills_csv,
            skill_categories_csv,
            has_salary_info
        FROM dbo.vw_job_matching
        WHERE job_title IS NOT NULL
        ORDER BY has_salary_info DESC, posted_date DESC, job_posting_key DESC;
    """
    try:
        with pyodbc.connect(connection_string, timeout=seed_timeout) as connection:
            cursor = connection.cursor()
            cursor.timeout = seed_timeout
            rows = cursor.execute(query).fetchall()
    except Exception:
        return
    for index, row in enumerate(rows, start=1):
        skills = [item.strip().lower() for item in str(row.skills_csv or "").split(",") if item.strip()][:10]
        if not skills:
            skills = ["sql", "python"] if "data" in str(row.category_name or "").lower() else ["communication"]
        salary = float(row.salary_year_avg) if row.salary_year_avg is not None else None
        company_id = company_ids[index % len(company_ids)]
        segment_name = clean_segment_label(str(row.skill_categories_csv or row.category_name or "General IT"))
        job_id = store.next_id("job")
        store.jobs[job_id] = {
            "id": job_id,
            "warehouse_source": True,
            "company_id": company_id,
            "source_company_name": row.company_name,
            "title": str(row.job_title or "Untitled job"),
            "category": str(row.category_name or "IT Job"),
            "country": str(row.country or "Unknown"),
            "city": str(row.city or "Unknown"),
            "remote": bool(row.is_work_from_home),
            "work_mode": "remote" if bool(row.is_work_from_home) else "onsite/hybrid",
            "schedule_type": str(row.schedule_types_csv or "Full-time"),
            "experience_level": "senior" if "senior" in str(row.job_title or "").lower() else "junior" if "junior" in str(row.job_title or "").lower() else "mid",
            "description": f"Warehouse job imported from SQL for {row.category_name or 'IT'} roles. Required skills include {', '.join(skills[:5])}.",
            "required_skills": skills,
            "salary_year_avg": salary,
            "estimated_salary_range": [int(salary * 0.9), int(salary * 1.12)] if salary else None,
            "classification": {"remote_class": "remote" if bool(row.is_work_from_home) else "onsite/hybrid", "schedule_class": str(row.schedule_types_csv or "Unknown"), "confidence": 76},
            "segmentation": {"segment_name": segment_name, "cluster_id": index % 7, "confidence": 68},
            "status": "published",
            "created_by": recruiter_id,
            "created_at": now_iso(),
        }


def clean_segment_label(value: str) -> str:
    parts = []
    seen = set()
    for item in value.replace(";", ",").split(","):
        label = item.strip()
        key = label.lower()
        if label and key not in seen:
            seen.add(key)
            parts.append(label)
    return ", ".join(parts[:3]) or "General IT"

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Backend.TalentBridgeAPI.app.platform.routers.application_routes import apply_to_job
from Backend.TalentBridgeAPI.app.platform.routers.matching_routes import candidate_job_matches, job_candidate_matches
from Backend.TalentBridgeAPI.app.platform.routers.shortlist_routes import add_to_shortlist
from Backend.TalentBridgeAPI.app.platform.schemas import ApplicationCreateRequest
from Backend.TalentBridgeAPI.app.platform.store import seed_platform, store


def user_by_role(role: str) -> dict:
    return next(user for user in store.users.values() if user["role"] == role)


def main() -> None:
    seed_platform()
    candidate = user_by_role("candidate")
    recruiter = user_by_role("recruiter")
    admin = user_by_role("admin")

    jobs = [job for job in store.jobs.values() if job["status"] == "published"]
    assert jobs, "candidate should see published jobs"

    matches = candidate_job_matches(candidate)["matches"]
    assert matches, "candidate should receive job matches"

    cv_id = store.next_id("cv")
    store.cv_documents[cv_id] = {"id": cv_id, "owner_id": candidate["id"], "file_name": "demo_cv.pdf", "uploaded_at": "test", "extraction": {"skills": ["python", "sql"]}, "quality": {"quality_score": 88, "quality_label": "Pro"}}

    existing = next((item for item in store.applications.values() if item["candidate_id"] == candidate["id"] and item["job_id"] == jobs[0]["id"]), None)
    application = existing or apply_to_job(ApplicationCreateRequest(job_id=jobs[0]["id"], cv_id=cv_id), candidate)["application"]
    assert application["status"] in {"Applied", "UnderReview", "InterviewRequested", "Accepted", "Rejected", "shortlisted"}

    recruiter_matches = job_candidate_matches(jobs[0]["id"], recruiter)["matches"]
    assert recruiter_matches, "recruiter should receive candidate matches"

    shortlist = add_to_shortlist(jobs[0]["id"], candidate["id"], recruiter)["shortlist_item"]
    assert shortlist["candidate_id"] == candidate["id"]

    assert admin["role"] == "admin"
    print("platform workflows passed")


if __name__ == "__main__":
    main()

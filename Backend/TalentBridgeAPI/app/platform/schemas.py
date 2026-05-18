from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["candidate", "recruiter", "admin"]
ApplicationStatus = Literal[
    "submitted", "viewed", "shortlisted", "interview", "offer", "rejected", "withdrawn", "hired",
    "Applied", "UnderReview", "InterviewRequested", "InterviewTimeProposed", "InterviewSlotsDeclined", "Accepted", "Rejected",
]
JobStatus = Literal["draft", "published", "closed"]
AiJobStatus = Literal["queued", "running", "succeeded", "failed", "retrying"]


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    role: Role


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class CandidateProfileUpdate(BaseModel):
    title: str | None = None
    location: str | None = None
    preferred_roles: list[str] = []
    preferred_country: str | None = None
    skills: list[str] = []
    education: list[str] = []
    experience_summary: str | None = None
    visibility: bool = True


class RecruiterProfileUpdate(BaseModel):
    title: str | None = None
    phone: str | None = None
    company_id: int | None = None


class CompanyCreateRequest(BaseModel):
    name: str
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    description: str | None = None


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    description: str | None = None


class JobCreateRequest(BaseModel):
    company_id: int
    title: str
    category: str
    country: str | None = None
    city: str | None = None
    remote: bool = False
    schedule_type: str = "Full-time"
    description: str | None = None
    required_skills: list[str] = []
    salary_year_avg: float | None = None


class JobUpdateRequest(BaseModel):
    title: str | None = None
    category: str | None = None
    country: str | None = None
    city: str | None = None
    remote: bool | None = None
    schedule_type: str | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    salary_year_avg: float | None = None


class ApplicationCreateRequest(BaseModel):
    job_id: int
    cv_id: int | None = None
    cover_letter: str | None = None


class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus
    note: str | None = None


class InterviewSlotProposalRequest(BaseModel):
    slots: list[str] = Field(min_length=1)
    note: str | None = None


class InterviewSlotSelectionRequest(BaseModel):
    slot_id: str


class InterviewSlotDeclineRequest(BaseModel):
    reason: str | None = None


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: str = "info"


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

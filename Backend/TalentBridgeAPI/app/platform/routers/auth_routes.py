from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import AuthResponse, LoginRequest, RegisterRequest, now_iso
from ..security import current_user
from ..store import hash_password, save_platform_store, store


router = APIRouter(prefix="/auth", tags=["Auth"])


def public_user(user: dict) -> dict:
    return {key: value for key, value in user.items() if key != "password_hash"}


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    if any(user["email"].lower() == payload.email.lower() for user in store.users.values()):
        raise HTTPException(status_code=409, detail="Email already registered")
    user_id = store.next_id("user")
    user = {"id": user_id, "email": payload.email.lower(), "password_hash": hash_password(payload.password), "full_name": payload.full_name, "role": payload.role, "status": "active", "created_at": now_iso()}
    store.users[user_id] = user
    if payload.role == "candidate":
        store.candidate_profiles[user_id] = {"user_id": user_id, "title": None, "location": None, "preferred_roles": [], "preferred_country": None, "skills": [], "education": [], "experience_summary": None, "visibility": True}
    if payload.role == "recruiter":
        store.recruiter_profiles[user_id] = {"user_id": user_id, "title": None, "phone": None, "company_id": None}
    token = store.create_token(user_id)
    store.audit(user_id, "register", "user", user_id)
    save_platform_store()
    return AuthResponse(access_token=token, user=public_user(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    password_hash = hash_password(payload.password)
    user = next((item for item in store.users.values() if item["email"].lower() == payload.email.lower() and item["password_hash"] == password_hash), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = store.create_token(user["id"])
    store.audit(user["id"], "login", "user", user["id"])
    return AuthResponse(access_token=token, user=public_user(user))


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": public_user(user)}

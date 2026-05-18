from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from .store import store


ROLE_PERMISSIONS = {
    "candidate": {"candidate", "authenticated"},
    "recruiter": {"recruiter", "authenticated"},
    "admin": {"admin", "candidate", "recruiter", "authenticated"},
}


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = store.tokens.get(token)
    if not user_id or user_id not in store.users:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = store.users[user_id]
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def require_role(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

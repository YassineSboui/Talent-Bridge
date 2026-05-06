from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..security import current_user
from ..store import save_platform_store, store


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(user: dict = Depends(current_user)):
    return {"notifications": [item for item in store.notifications.values() if item["user_id"] == user["id"]]}


@router.get("/my")
def my_notifications(user: dict = Depends(current_user)):
    return list_notifications(user)


@router.patch("/{notification_id}/read")
def mark_read(notification_id: int, user: dict = Depends(current_user)):
    notification = store.notifications.get(notification_id)
    if not notification or notification["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification["read"] = True
    save_platform_store()
    return {"notification": notification}


@router.put("/{notification_id}/read")
def put_mark_read(notification_id: int, user: dict = Depends(current_user)):
    return mark_read(notification_id, user)


@router.post("/read-all")
def mark_all_read(user: dict = Depends(current_user)):
    count = 0
    for notification in store.notifications.values():
        if notification["user_id"] == user["id"]:
            notification["read"] = True
            count += 1
    save_platform_store()
    return {"updated": count}

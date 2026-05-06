from __future__ import annotations

from fastapi import APIRouter

from .routers.admin_routes import router as admin_router
from .routers.application_routes import router as application_router
from .routers.auth_routes import router as auth_router
from .routers.company_routes import router as company_router
from .routers.cv_routes import router as cv_router
from .routers.candidate_routes import router as candidate_router
from .routers.job_routes import router as job_router
from .routers.matching_routes import router as matching_router
from .routers.notification_routes import router as notification_router
from .routers.profile_routes import router as profile_router
from .routers.shortlist_routes import router as shortlist_router


api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(company_router)
api_v1_router.include_router(job_router)
api_v1_router.include_router(cv_router)
api_v1_router.include_router(candidate_router)
api_v1_router.include_router(matching_router)
api_v1_router.include_router(application_router)
api_v1_router.include_router(shortlist_router)
api_v1_router.include_router(notification_router)
api_v1_router.include_router(admin_router)

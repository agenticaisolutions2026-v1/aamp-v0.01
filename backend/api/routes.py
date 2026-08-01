from fastapi import APIRouter

from backend.api.home import router as home_router
from backend.api.health import router as health_router
from backend.api.version import router as version_router

router = APIRouter()

router.include_router(home_router)
router.include_router(health_router)
router.include_router(version_router)
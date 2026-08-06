from fastapi import APIRouter

from backend.api.home import router as home_router
from backend.api.health import router as health_router
from backend.api.version import router as version_router

from backend.api.organizations import router as organizations_router
from backend.api.campaigns import router as campaigns_router
from backend.api.agents import router as agents_router

router = APIRouter()

router.include_router(home_router)
router.include_router(health_router)
router.include_router(version_router)

router.include_router(organizations_router)
router.include_router(campaigns_router)
router.include_router(agents_router)
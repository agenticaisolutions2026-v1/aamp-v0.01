from fastapi import APIRouter

from .health import router as health_router
from .organizations import router as organizations_router
from .campaigns import router as campaigns_router
from .agents import router as agents_router
from .colleges import router as colleges_router
from .outreach import router as outreach_router
from .demo import router as demo_router


api_router = APIRouter()


api_router.include_router(
    health_router,
    tags=["health"],
)


api_router.include_router(
    organizations_router,
    tags=["organizations"],
)


api_router.include_router(
    campaigns_router,
    tags=["campaigns"],
)


api_router.include_router(
    agents_router,
    tags=["agents"],
)


api_router.include_router(
    colleges_router,
    tags=["colleges"],
)


api_router.include_router(
    outreach_router,
    tags=["outreach"],
)


api_router.include_router(
    demo_router,
    tags=["demo"],
)
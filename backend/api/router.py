from fastapi import APIRouter

from backend.api.v1.api import api_router

router = APIRouter()

router.include_router(
    api_router,
    prefix="/api/v1"
)
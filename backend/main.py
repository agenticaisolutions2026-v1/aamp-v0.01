from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.clients.http_client import http_client
from backend.api.router import router as api_router
from backend.scheduler.campaign_scheduler import CampaignScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Start campaign scheduler
    campaign_scheduler = CampaignScheduler()
    campaign_scheduler.start()

    # Store scheduler in FastAPI application state
    app.state.campaign_scheduler = campaign_scheduler

    try:
        yield

    finally:
        # Stop campaign scheduler
        campaign_scheduler.shutdown()

        # Close HTTP client
        await http_client.aclose()


app = FastAPI(
    title="AAMP Backend API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)


@app.get("/api/v1")
def root():
    return {"message": "Welcome to AAMP"}
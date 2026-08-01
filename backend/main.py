from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(
    title="Agentic AI Marketing Platform",
    version="0.0.1"
)

app.include_router(router)
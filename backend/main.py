from contextlib import asynccontextmanager
from backend.clients.http_client import http_client

from fastapi import FastAPI

from backend.api.router import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()
    
app = FastAPI(
    title="AAMP Backend API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)
@app.get("/api/v1")
def root():
     return{"message" : "Welcome to AAMP"}
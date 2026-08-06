from fastapi import FastAPI

from backend.api.router import router

app = FastAPI(
    title="AAMP Backend API",
    version="1.0.0"
)

app.include_router(
    router)
@app.get("/api/v1")
def root():
     return{"message" : "Welcome to AAMP"}
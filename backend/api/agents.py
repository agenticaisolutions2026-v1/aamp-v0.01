from fastapi import APIRouter
from backend.schemas.agent import AgentResponse

router = APIRouter()


@router.get("/agents", response_model=list[AgentResponse])
def get_agents():
    return [
        {
            "id": 1,
            "name": "Supervisor Agent",
            "status": "Running"
        },
        {
            "id": 2,
            "name": "Marketing Agent",
            "status": "Running"
        },
        {
            "id": 3,
            "name": "Analytics Agent",
            "status": "Idle"
        }
    ]
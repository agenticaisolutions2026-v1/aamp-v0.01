from fastapi import APIRouter


router = APIRouter()


@router.get("/agents")
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
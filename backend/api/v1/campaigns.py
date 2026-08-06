from fastapi import APIRouter


router = APIRouter()


@router.get("/campaigns")
def get_campaigns():
    return [
        {
            "id": 1,
            "name": "AI Marketing Campaign",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Email Campaign",
            "status": "Completed"
        },
        {
            "id": 3,
            "name": "Social Media Campaign",
            "status": "Draft"
        }
    ]
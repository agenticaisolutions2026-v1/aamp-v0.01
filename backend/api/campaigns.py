from fastapi import APIRouter
from backend.schemas.campaign import CampaignResponse

router = APIRouter()


@router.get("/campaigns", response_model=list[CampaignResponse])
def get_campaigns():
    return [
        {
            "id": 1,
            "name": "AI Workshop",
            "department": "AI & ML",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Placement Drive",
            "department": "Computer Science",
            "status": "Completed"
        },
        {
            "id": 3,
            "name": "Internship Program",
            "department": "ECE",
            "status": "Upcoming"
        }
    ]
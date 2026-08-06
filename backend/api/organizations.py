from fastapi import APIRouter
from backend.schemas.organization import OrganizationResponse

router = APIRouter()


@router.get("/organizations", response_model=list[OrganizationResponse])
def get_organizations():
    return [
        {
            "id": 1,
            "name": "VNR VJIET",
            "state": "Telangana"
        },
        {
            "id": 2,
            "name": "CBIT",
            "state": "Telangana"
        },
        {
            "id": 3,
            "name": "KL University",
            "state": "Andhra Pradesh"
        }
    ]
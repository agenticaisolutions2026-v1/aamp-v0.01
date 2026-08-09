from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.database.models import Organization

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)

@router.get("")
async def get_organizations(db: Session = Depends(get_db)):
    organizations = db.query(Organization).all()

    return [
        {
            "id": organization.id,
            "name": organization.name,
            "state": organization.state
        }
        for organization in organizations
    ]


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models import Organization


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.get("")
async def get_organizations(db: Session = Depends(get_db)):
    organizations = (
        db.query(Organization)
        .order_by(Organization.created_at.desc())
        .all()
    )

    return [
        {
            "id": organization.id,
            "name": organization.name,
            "created_at": organization.created_at,
            "updated_at": organization.updated_at,
        }
        for organization in organizations
    ]


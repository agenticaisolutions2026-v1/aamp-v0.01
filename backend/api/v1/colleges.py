from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.database.models import College


router = APIRouter(
    prefix="/colleges",
    tags=["Colleges"],
)


@router.get("")
async def get_colleges(
    db: Session = Depends(get_db),
):
    colleges = db.query(College).all()

    return [
        {
            "id": college.id,
            "name": college.name,
            "website": college.website,
            "state": college.state,
            "city": college.city,
            "address": college.address,
            "phone": college.phone,
            "email": college.email,
            "departments": college.departments,
            "programs": college.programs,
            "placement_page": college.placement_page,
            "contact_page": college.contact_page,
            "source_url": college.source_url,
        }
        for college in colleges
    ]
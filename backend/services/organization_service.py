from sqlalchemy.orm import Session

from backend.database.models import Organization


class OrganizationService:

    @staticmethod
    def get_all(db: Session):
        return db.query(Organization).all()
from sqlalchemy.orm import Session

from backend.models.lead import Lead


class LeadRepository:

    @staticmethod
    def create(db: Session, lead: Lead):
        db.add(lead)
        db.flush()
        return lead

    @staticmethod
    def get_all(db: Session):
        return db.query(Lead).all()

    @staticmethod
    def get_by_id(
        db: Session,
        lead_id: int,
    ):
        return (
            db.query(Lead)
            .filter(Lead.id == lead_id)
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        lead: Lead,
        data: dict,
    ):
        for field, value in data.items():
            setattr(lead, field, value)

        db.flush()
        return lead
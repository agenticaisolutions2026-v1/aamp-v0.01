from sqlalchemy.orm import Session

from backend.models.campaign import Campaign


class CampaignRepository:

    @staticmethod
    def create(db: Session, campaign: Campaign):
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def get_all(db: Session):
        return db.query(Campaign).all()

    @staticmethod
    def get_by_id(db: Session, campaign_id: int):
        return (
            db.query(Campaign)
            .filter(Campaign.id == campaign_id)
            .first()
        )

    @staticmethod
    def update(db: Session, campaign: Campaign):
        db.commit()
        db.refresh(campaign)
        return campaign
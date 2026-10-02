from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.models import Outreach


class OutreachPersistenceService:

    @staticmethod
    def save_outreach(
        db: Session,
        outreach_data: dict,
    ):
        outreach = Outreach(
            campaign_id=outreach_data.get("campaign_id"),
            college_id=outreach_data.get("college_id"),
            channel=outreach_data.get("channel", "manual_review"),
            recipient=outreach_data.get("recipient"),
            subject=outreach_data.get("subject"),
            message=outreach_data.get("message", ""),
            status=outreach_data.get("status", "queued"),
            scheduled_at=outreach_data.get("scheduled_at"),
            sent_at=outreach_data.get("sent_at"),
            response_received_at=outreach_data.get(
                "response_received_at"
            ),
            follow_up_count=outreach_data.get(
                "follow_up_count",
                0,
            ),
            last_error=outreach_data.get("last_error"),
            created_at=outreach_data.get(
                "created_at",
                datetime.utcnow(),
            ),
        )

        db.add(outreach)
        db.commit()
        db.refresh(outreach)

        return outreach

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(Outreach)
            .order_by(Outreach.id.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        outreach_id: int,
    ):
        return (
            db.query(Outreach)
            .filter(Outreach.id == outreach_id)
            .first()
        )
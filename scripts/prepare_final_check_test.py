from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models.campaign import Campaign


CAMPAIGN_ID = 26


def main():

    with Session(engine) as session:

        campaign = session.scalar(
            select(Campaign).where(
                Campaign.id == CAMPAIGN_ID
            )
        )

        if campaign is None:
            raise ValueError(
                f"Campaign not found: {CAMPAIGN_ID}"
            )

        now = datetime.now(timezone.utc)

        campaign.status = "sent"
        campaign.follow_up_count = 2
        campaign.max_follow_ups = 2
        campaign.last_response_at = None
        campaign.response_category = None
        campaign.completed_at = None
        campaign.failure_reason = None

        # Make final response check immediately due
        campaign.next_follow_up_at = (
            now - timedelta(minutes=5)
        )

        session.commit()

        print("\n========================================")
        print("FINAL RESPONSE CHECK TEST PREPARED")
        print("========================================")
        print(f"Campaign ID       : {campaign.id}")
        print(f"Status            : {campaign.status}")
        print(f"Follow-up Count   : {campaign.follow_up_count}")
        print(f"Max Follow-ups    : {campaign.max_follow_ups}")
        print(f"Next Follow-up    : {campaign.next_follow_up_at}")
        print(f"Last Response     : {campaign.last_response_at}")
        print("========================================\n")


if __name__ == "__main__":
    main()
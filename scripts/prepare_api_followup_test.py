from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models.campaign import Campaign


CAMPAIGN_ID = 24


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
        campaign.channel = "email"

        # Simulate initial outreach already sent.
        campaign.sent_at = now - timedelta(days=1)

        campaign.follow_up_count = 0
        campaign.max_follow_ups = 2

        # Make Follow-up #1 immediately due.
        campaign.next_follow_up_at = (
            now - timedelta(minutes=5)
        )

        campaign.last_response_at = None
        campaign.response_category = None
        campaign.completed_at = None
        campaign.failure_reason = None

        session.commit()

        print("\n========================================")
        print("API FOLLOW-UP TEST PREPARED")
        print("========================================")
        print(f"Campaign ID       : {campaign.id}")
        print(f"College ID        : {campaign.college_id}")
        print(f"Status            : {campaign.status}")
        print(f"Channel           : {campaign.channel}")
        print(f"Sent At           : {campaign.sent_at}")
        print(f"Next Follow-up    : {campaign.next_follow_up_at}")
        print(f"Follow-up Count   : {campaign.follow_up_count}")
        print(f"Max Follow-ups    : {campaign.max_follow_ups}")
        print(f"Last Response     : {campaign.last_response_at}")
        print("========================================\n")


if __name__ == "__main__":
    main()
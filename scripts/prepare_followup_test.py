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
                f"Campaign {CAMPAIGN_ID} not found."
            )

        # --------------------------------------------------
        # Prepare controlled follow-up test state
        # --------------------------------------------------

        now = datetime.now(timezone.utc)

        campaign.status = "sent"
        campaign.channel = "email"

        # Pretend initial email was sent yesterday.
        campaign.sent_at = now - timedelta(days=1)

        # Make follow-up immediately due.
        campaign.next_follow_up_at = (
            now - timedelta(minutes=5)
        )

        campaign.follow_up_count = 0
        campaign.max_follow_ups = 2

        # No response.
        campaign.last_response_at = None
        campaign.response_category = None

        campaign.completed_at = None
        campaign.failure_reason = None

        session.commit()

        print("\n========================================")
        print("FOLLOW-UP TEST PREPARED")
        print("========================================")

        print(f"Campaign ID       : {campaign.id}")
        print(f"Status            : {campaign.status}")
        print(f"Channel           : {campaign.channel}")
        print(f"Sent At           : {campaign.sent_at}")
        print(
            f"Next Follow-up    : "
            f"{campaign.next_follow_up_at}"
        )
        print(
            f"Follow-up Count   : "
            f"{campaign.follow_up_count}"
        )
        print(
            f"Max Follow-ups    : "
            f"{campaign.max_follow_ups}"
        )
        print(
            f"Last Response     : "
            f"{campaign.last_response_at}"
        )

        print("========================================")


if __name__ == "__main__":
    main()
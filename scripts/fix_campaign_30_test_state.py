from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models.campaign import Campaign


CAMPAIGN_ID = 30
IST = ZoneInfo("Asia/Kolkata")


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

        print("\n========== BEFORE CLEANUP ==========")
        print("Campaign ID:", campaign.id)
        print("Status:", campaign.status)
        print("Response Category:", campaign.response_category)
        print("Follow-up Count:", campaign.follow_up_count)
        print("Next Follow-up:", campaign.next_follow_up_at)

        # ----------------------------------------------
        # Set the correct 3-day response deadline
        # ----------------------------------------------

        campaign.status = "sent"
        campaign.follow_up_count = 1

        campaign.next_follow_up_at = datetime(
            2026,
            9,
            29,
            9,
            30,
            0,
            tzinfo=IST,
        )

        session.commit()
        session.refresh(campaign)

        print("\n========== AFTER CLEANUP ==========")
        print("Campaign ID:", campaign.id)
        print("Status:", campaign.status)
        print("Response Category:", campaign.response_category)
        print("Follow-up Count:", campaign.follow_up_count)
        print("Next Follow-up:", campaign.next_follow_up_at)


if __name__ == "__main__":
    main()
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models.campaign import Campaign
from backend.services.follow_up_service import FollowUpService


CAMPAIGN_ID = 30


def main():

    follow_up_service = FollowUpService()

    # --------------------------------------------------
    # 1. Save original campaign state
    # --------------------------------------------------

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

        original_next_follow_up_at = (
            campaign.next_follow_up_at
        )

        original_status = campaign.status
        original_follow_up_count = (
            campaign.follow_up_count
        )

        print("\n========== BEFORE TEST ==========")
        print(
            "Campaign ID:",
            campaign.id,
        )
        print(
            "Status:",
            campaign.status,
        )
        print(
            "Response Category:",
            campaign.response_category,
        )
        print(
            "Follow-up Count:",
            campaign.follow_up_count,
        )
        print(
            "Next Follow-up:",
            campaign.next_follow_up_at,
        )

        # --------------------------------------------------
        # 2. Force follow-up to be due NOW
        # --------------------------------------------------

        campaign.next_follow_up_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        )

        session.commit()

        print(
            "\nTEST: next_follow_up_at temporarily "
            "moved into the past."
        )


    # --------------------------------------------------
    # 3. Process due follow-ups
    # --------------------------------------------------

    try:

        print("\n========== PROCESSING ==========")

        results = (
            follow_up_service
            .process_due_followups()
        )

        print(
            "Processed:",
            len(results),
        )

        for result in results:
            print(
                "\nResult:",
                result,
            )

    finally:

        # --------------------------------------------------
        # 4. Restore original timestamp
        # --------------------------------------------------

        with Session(engine) as session:

            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == CAMPAIGN_ID
                )
            )

            if campaign is not None:

                campaign.next_follow_up_at = (
                    original_next_follow_up_at
                )

                session.commit()

                print(
                    "\n========== RESTORED =========="
                )
                print(
                    "Original next_follow_up_at:",
                    original_next_follow_up_at,
                )


    # --------------------------------------------------
    # 5. Show final state
    # --------------------------------------------------

    with Session(engine) as session:

        campaign = session.scalar(
            select(Campaign).where(
                Campaign.id == CAMPAIGN_ID
            )
        )

        if campaign is not None:

            print("\n========== AFTER TEST ==========")
            print(
                "Status:",
                campaign.status,
            )
            print(
                "Response Category:",
                campaign.response_category,
            )
            print(
                "Follow-up Count:",
                campaign.follow_up_count,
            )
            print(
                "Next Follow-up:",
                campaign.next_follow_up_at,
            )


if __name__ == "__main__":
    main()
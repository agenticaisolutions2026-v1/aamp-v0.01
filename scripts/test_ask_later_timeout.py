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
    # 1. Save current state
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

        print("\n========== BEFORE TIMEOUT TEST ==========")
        print("Campaign ID:", campaign.id)
        print("Status:", campaign.status)
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
        # 2. Temporarily make the 3-day deadline due
        # --------------------------------------------------

        campaign.next_follow_up_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        )

        session.commit()

        print(
            "\nTEST: 3-day response deadline "
            "temporarily moved into the past."
        )

    # --------------------------------------------------
    # 3. Process due follow-ups
    # --------------------------------------------------

    try:

        print("\n========== PROCESSING TIMEOUT ==========")

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
        # 4. Do NOT restore the old timestamp
        #
        # The expected result is campaign completion.
        # --------------------------------------------------

        print(
            "\n========== TIMEOUT TEST COMPLETE =========="
        )

    # --------------------------------------------------
    # 5. Read final campaign state
    # --------------------------------------------------

    with Session(engine) as session:

        campaign = session.scalar(
            select(Campaign).where(
                Campaign.id == CAMPAIGN_ID
            )
        )

        if campaign is not None:

            print("\n========== AFTER TIMEOUT TEST ==========")
            print("Status:", campaign.status)
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
            print(
                "Completed At:",
                campaign.completed_at,
            )


if __name__ == "__main__":
    main()
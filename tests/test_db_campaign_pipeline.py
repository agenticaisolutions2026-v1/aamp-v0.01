from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import Lead
from backend.services.college_pipeline_service import (
    CollegePipelineService,
)


def main():

    print("=" * 70)
    print("CREATING CAMPAIGN DRAFTS FOR QUALIFIED LEADS")
    print("=" * 70)

    service = CollegePipelineService()

    # --------------------------------------------------
    # Find qualified leads without existing campaigns
    # --------------------------------------------------

    with Session(engine) as session:

        qualified_leads = session.scalars(
            select(Lead)
            .where(
                Lead.qualification == "qualified"
            )
            .order_by(Lead.id)
        ).all()

        lead_ids = [
            lead.id
            for lead in qualified_leads
        ]

    print(
        f"Qualified leads found: {len(lead_ids)}"
    )

    print()

    # --------------------------------------------------
    # Generate campaigns
    # --------------------------------------------------

    created = 0
    failed = 0

    for index, lead_id in enumerate(
        lead_ids,
        start=1,
    ):

        print(
            f"[{index}/{len(lead_ids)}] "
            f"Processing lead_id: {lead_id}"
        )

        try:

            campaign = (
                service.generate_campaign_for_lead(
                    lead_id
                )
            )

            created += 1

            print(
                f"  ✓ Campaign generated"
            )

            print(
                f"    College ID    : "
                f"{campaign.get('college_id')}"
            )

            print(
                f"    College Name  : "
                f"{campaign.get('college_name')}"
            )

            print(
                f"    Campaign Type : "
                f"{campaign.get('campaign_type')}"
            )

            print(
                f"    Message Type  : "
                f"{campaign.get('message_type')}"
            )

            print(
                f"    Status        : "
                f"{campaign.get('status', 'draft')}"
            )

        except Exception as exc:

            failed += 1

            print(
                f"  ✗ Failed: {exc}"
            )

        print()

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("=" * 70)
    print("CAMPAIGN GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Qualified leads : {len(lead_ids)}"
    )

    print(
        f"Created         : {created}"
    )

    print(
        f"Failed          : {failed}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
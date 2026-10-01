from backend.services.campaign_review_service import (
    CampaignReviewService,
)


def main():
    print("=" * 70)
    print("TESTING CAMPAIGN HUMAN REVIEW")
    print("=" * 70)

    campaign_id = 4

    print(f"Processing campaign_id: {campaign_id}")

    service = CampaignReviewService()

    campaign = service.approve_campaign(
        campaign_id=campaign_id,
        approved_by="Naresh",
        reason="Campaign content reviewed and approved.",
    )

    print()
    print("-" * 70)
    print("CAMPAIGN APPROVED")
    print("-" * 70)

    print(f"Campaign ID       : {campaign.id}")
    print(f"College ID        : {campaign.college_id}")
    print(f"Campaign Type     : {campaign.campaign_type}")
    print(f"Message Type      : {campaign.message_type}")
    print(f"Channel           : {campaign.channel}")
    print(f"Priority          : {campaign.priority}")
    print(f"Status            : {campaign.status}")
    print(f"Required Approval : {campaign.required_approval}")
    print(f"Approved At       : {campaign.approved_at}")
    print()
    print(f"Subject           : {campaign.subject}")

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
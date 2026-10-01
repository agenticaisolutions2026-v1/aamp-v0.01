from backend.services.campaign_service import CampaignService


def main():
    print("=" * 70)
    print("TESTING CAMPAIGN SERVICE")
    print("=" * 70)

    service = CampaignService()

    # ----------------------------------
    # Get one campaign
    # ----------------------------------

    print()
    print("1. GET CAMPAIGN BY ID")
    print("-" * 70)

    campaign = service.get_campaign(4)

    print(f"Campaign ID       : {campaign.id}")
    print(f"College ID        : {campaign.college_id}")
    print(f"Campaign Type     : {campaign.campaign_type}")
    print(f"Message Type      : {campaign.message_type}")
    print(f"Channel           : {campaign.channel}")
    print(f"Priority          : {campaign.priority}")
    print(f"Status            : {campaign.status}")
    print(f"Required Approval : {campaign.required_approval}")
    print(f"Approved At       : {campaign.approved_at}")

    # ----------------------------------
    # Get all campaigns
    # ----------------------------------

    print()
    print("2. GET ALL CAMPAIGNS")
    print("-" * 70)

    campaigns = service.get_all_campaigns()

    print(f"Total campaigns: {len(campaigns)}")

    for item in campaigns:
        print(
            f"ID={item.id} | "
            f"College={item.college_id} | "
            f"Type={item.message_type} | "
            f"Status={item.status}"
        )

    # ----------------------------------
    # Get campaigns by status
    # ----------------------------------

    print()
    print("3. GET APPROVED CAMPAIGNS")
    print("-" * 70)

    approved_campaigns = service.get_campaigns_by_status(
        "approved"
    )

    print(
        f"Approved campaigns: "
        f"{len(approved_campaigns)}"
    )

    for item in approved_campaigns:
        print(
            f"ID={item.id} | "
            f"College={item.college_id} | "
            f"Status={item.status}"
        )

    # ----------------------------------
    # Test draft status
    # ----------------------------------

    print()
    print("4. GET DRAFT CAMPAIGNS")
    print("-" * 70)

    draft_campaigns = service.get_campaigns_by_status(
        "draft"
    )

    print(
        f"Draft campaigns: "
        f"{len(draft_campaigns)}"
    )

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
from backend.services.follow_up_service import FollowUpService


def main():

    service = FollowUpService()

    print("\n========================================")
    print("FOLLOW-UP SERVICE TEST")
    print("========================================")

    # ------------------------------------------
    # Check due follow-ups
    # ------------------------------------------

    campaigns = service.get_due_followups()

    print(f"\nDue follow-ups: {len(campaigns)}")

    for campaign in campaigns:

        print("\n----------------------------------------")
        print(f"Campaign ID       : {campaign.id}")
        print(f"College ID        : {campaign.college_id}")
        print(f"Status            : {campaign.status}")
        print(f"Sent At           : {campaign.sent_at}")
        print(f"Next Follow-up    : {campaign.next_follow_up_at}")
        print(f"Follow-up Count   : {campaign.follow_up_count}")
        print(f"Max Follow-ups    : {campaign.max_follow_ups}")
        print(f"Last Response     : {campaign.last_response_at}")
        print(f"Response Category : {campaign.response_category}")

    # ------------------------------------------
    # Process due follow-ups
    # ------------------------------------------

    if campaigns:

        print("\n========================================")
        print("PROCESSING DUE FOLLOW-UPS")
        print("========================================")

        results = service.process_due_followups()

        for result in results:

            print("\n----------------------------------------")
            print(f"Campaign ID       : {result.get('campaign_id')}")
            print(f"Status            : {result.get('status')}")

            if result.get("follow_up_count") is not None:
                print(
                    f"Follow-up Count   : "
                    f"{result.get('follow_up_count')}"
                )

            if result.get("next_follow_up_at") is not None:
                print(
                    f"Next Follow-up    : "
                    f"{result.get('next_follow_up_at')}"
                )

            if result.get("reason"):
                print(
                    f"Reason            : "
                    f"{result.get('reason')}"
                )

            if result.get("error"):
                print(
                    f"Error             : "
                    f"{result.get('error')}"
                )

    else:

        print("\nNo follow-ups are currently due.")


if __name__ == "__main__":
    main()
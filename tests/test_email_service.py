from backend.services.email_service import EmailService


def main():
    print("=" * 70)
    print("TESTING CAMPAIGN EMAIL SERVICE")
    print("=" * 70)

    campaign_id = 4

    print(f"Campaign ID : {campaign_id}")
    print("Test mode   : TRUE")
    print("Recipient   : EMAIL_TEST_RECIPIENT")
    print()
    print("Sending test email...")
    print()

    service = EmailService()

    result = service.send_campaign_email(
        campaign_id=campaign_id
    )

    print("-" * 70)
    print("EMAIL RESULT")
    print("-" * 70)

    print(f"Campaign ID : {result['campaign_id']}")
    print(f"College     : {result['college_name']}")
    print(f"Recipient   : {result['recipient']}")
    print(f"Subject     : {result['subject']}")
    print(f"Test Mode   : {result['test_mode']}")
    print(f"Sent        : {result['sent']}")
    print(f"Status      : {result['status']}")

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("EMAIL_SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD")
FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS")
FROM_NAME = os.getenv("EMAIL_FROM_NAME")


# Put YOUR OWN email address here for the test.
TEST_RECIPIENT = "naresh.near208@gmail.com"


email = EmailMessage()

email["From"] = f"{FROM_NAME} <{FROM_ADDRESS}>"
email["To"] = TEST_RECIPIENT
email["Subject"] = "AAMP SMTP Test"

email.set_content(
    """Hello,

This is a test email from the AAMP Gmail SMTP configuration.

No campaign was sent.

Regards,
AI & Quantum Training Team
"""
)


print("=" * 60)
print("AAMP GMAIL SMTP TEST")
print("=" * 60)

print(f"SMTP Host : {SMTP_HOST}")
print(f"SMTP Port : {SMTP_PORT}")
print(f"Username  : {SMTP_USERNAME}")
print(f"Recipient : {TEST_RECIPIENT}")
print()


try:

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
    ) as smtp:

        print("Connecting to Gmail SMTP...")

        smtp.starttls()

        print("STARTTLS successful.")

        smtp.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )

        print("SMTP authentication successful.")

        smtp.send_message(email)

        print("Email sent successfully.")

    print()
    print("=" * 60)
    print("SMTP TEST PASSED")
    print("=" * 60)

except Exception as exc:

    print()
    print("=" * 60)
    print("SMTP TEST FAILED")
    print("=" * 60)

    print(f"Error: {exc}")
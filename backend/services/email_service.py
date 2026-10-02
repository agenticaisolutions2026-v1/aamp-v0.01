import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailService:

    @staticmethod
    def send_email(
        sender_email: str,
        sender_password: str,
        receiver_email: str,
        subject: str,
        message: str,
    ) -> bool:

        email_message = MIMEMultipart()

        email_message["From"] = sender_email
        email_message["To"] = receiver_email
        email_message["Subject"] = subject

        email_message.attach(
            MIMEText(
                message,
                "plain",
            )
        )

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
        ) as server:

            server.starttls()

            server.login(
                sender_email,
                sender_password,
            )

            server.send_message(
                email_message
            )

        return True
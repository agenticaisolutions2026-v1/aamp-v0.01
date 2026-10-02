from datetime import datetime, timedelta


class DemoSchedulingService:
    """
    Handles demo scheduling for interested college responses.

    This service:
    - Provides available demo slots
    - Validates selected date/time
    - Creates a demo booking
    - Generates a confirmation message

    No external API or real email is used.
    """

    # =========================================================
    # AVAILABLE DEMO SLOTS
    # =========================================================

    @staticmethod
    def get_available_slots(days: int = 7):
        """
        Generate simple demo slots for the next few days.

        Demo slots:
        - 10:00 AM
        - 11:00 AM
        - 2:00 PM
        - 3:00 PM
        """

        slots = []

        today = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        slot_times = [
            (10, 0),
            (11, 0),
            (14, 0),
            (15, 0),
        ]

        for day_offset in range(1, days + 1):

            date_value = today + timedelta(
                days=day_offset
            )

            for hour, minute in slot_times:

                slot_datetime = date_value.replace(
                    hour=hour,
                    minute=minute,
                )

                slots.append(
                    {
                        "date": slot_datetime.strftime(
                            "%Y-%m-%d"
                        ),
                        "time": slot_datetime.strftime(
                            "%I:%M %p"
                        ),
                        "datetime": slot_datetime,
                    }
                )

        return slots

    # =========================================================
    # VALIDATE SLOT
    # =========================================================

    @staticmethod
    def validate_slot(
        selected_date: str,
        selected_time: str,
    ):
        """
        Validate a selected demo date and time.
        """

        try:

            selected_datetime = datetime.strptime(
                f"{selected_date} {selected_time}",
                "%Y-%m-%d %I:%M %p",
            )

        except ValueError:

            return {
                "valid": False,
                "reason": (
                    "Invalid date or time format. "
                    "Use YYYY-MM-DD and HH:MM AM/PM."
                ),
            }

        if selected_datetime <= datetime.now():

            return {
                "valid": False,
                "reason": (
                    "Demo date and time must be "
                    "in the future."
                ),
            }

        allowed_times = {
            "10:00 AM",
            "11:00 AM",
            "02:00 PM",
            "03:00 PM",
        }

        if selected_datetime.strftime(
            "%I:%M %p"
        ) not in allowed_times:

            return {
                "valid": False,
                "reason": (
                    "Selected time is not an available "
                    "demo slot."
                ),
            }

        return {
            "valid": True,
            "selected_datetime": selected_datetime,
        }

    # =========================================================
    # SCHEDULE DEMO
    # =========================================================

    @staticmethod
    def schedule_demo(
        college_name: str,
        recipient: str,
        selected_date: str,
        selected_time: str,
    ):
        """
        Schedule a demo locally.

        No calendar API or email API is called.
        """

        validation = (
            DemoSchedulingService.validate_slot(
                selected_date,
                selected_time,
            )
        )

        if not validation["valid"]:

            return {
                "status": "failed",
                "reason": validation["reason"],
            }

        selected_datetime = validation[
            "selected_datetime"
        ]

        confirmation_message = (
            f"Dear Sir/Madam,\n\n"
            f"Thank you for your interest in our AI "
            f"training program.\n\n"
            f"We are pleased to confirm the demo session "
            f"with {college_name}.\n\n"
            f"Demo Date: "
            f"{selected_datetime.strftime('%d-%m-%Y')}\n"
            f"Demo Time: "
            f"{selected_datetime.strftime('%I:%M %p')}\n\n"
            "We look forward to connecting with you and "
            "discussing the training program in detail.\n\n"
            "Regards,\n"
            "AI & Quantum Training Team"
        )

        return {
            "status": "scheduled",
            "college_name": college_name,
            "recipient": recipient,
            "demo_date": selected_datetime.strftime(
                "%Y-%m-%d"
            ),
            "demo_time": selected_datetime.strftime(
                "%I:%M %p"
            ),
            "scheduled_at": selected_datetime,
            "confirmation_message": (
                confirmation_message
            ),
            "real_message_sent": False,
        }
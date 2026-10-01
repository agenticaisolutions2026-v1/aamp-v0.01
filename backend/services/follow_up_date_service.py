from calendar import monthrange
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


class FollowUpDateService:

    DEFAULT_HOUR = 9
    DEFAULT_MINUTE = 30

    @staticmethod
    def calculate_follow_up_at(
        follow_up_hint: str,
        from_datetime: datetime | None = None,
    ) -> datetime:

        if from_datetime is None:
            from_datetime = datetime.now(IST)

        # Make sure datetime is timezone-aware
        if from_datetime.tzinfo is None:
            from_datetime = from_datetime.replace(tzinfo=IST)

        hint = (follow_up_hint or "unspecified").strip().lower()

        # ------------------------------------------
        # Relative days
        # ------------------------------------------

        if hint == "2_days":
            target_date = (
                from_datetime + timedelta(days=2)
            ).date()

        elif hint == "3_days":
            target_date = (
                from_datetime + timedelta(days=3)
            ).date()

        elif hint == "7_days":
            target_date = (
                from_datetime + timedelta(days=7)
            ).date()

        # ------------------------------------------
        # Next week
        # ------------------------------------------

        elif hint == "next_week":
            target_date = (
                from_datetime + timedelta(days=7)
            ).date()

        # ------------------------------------------
        # Next month
        # ------------------------------------------

        elif hint == "next_month":
            year = from_datetime.year
            month = from_datetime.month + 1

            if month > 12:
                month = 1
                year += 1

            # Keep the same day where possible.
            # If that day doesn't exist in the next month,
            # use the last day of the next month.
            last_day = monthrange(year, month)[1]

            day = min(
                from_datetime.day,
                last_day,
            )

            target_date = datetime(
                year,
                month,
                day,
                tzinfo=IST,
            ).date()

        # ------------------------------------------
        # No timing specified
        # ------------------------------------------

        elif hint == "unspecified":
            target_date = (
                from_datetime + timedelta(days=7)
            ).date()

        else:
            raise ValueError(
                f"Unsupported follow-up hint: {follow_up_hint}"
            )

        # ------------------------------------------
        # Follow-up time
        # ------------------------------------------

        return datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            FollowUpDateService.DEFAULT_HOUR,
            FollowUpDateService.DEFAULT_MINUTE,
            tzinfo=IST,
        )
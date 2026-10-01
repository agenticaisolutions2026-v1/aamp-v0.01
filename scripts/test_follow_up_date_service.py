from datetime import datetime
from zoneinfo import ZoneInfo

from backend.services.follow_up_date_service import (
    FollowUpDateService,
)


IST = ZoneInfo("Asia/Kolkata")


# Fixed date so our test is deterministic
test_datetime = datetime(
    2026,
    9,
    25,
    14,
    30,
    tzinfo=IST,
)


hints = [
    "2_days",
    "3_days",
    "7_days",
    "next_week",
    "next_month",
    "unspecified",
]


for hint in hints:

    result = FollowUpDateService.calculate_follow_up_at(
        follow_up_hint=hint,
        from_datetime=test_datetime,
    )

    print(
        f"{hint:15} → "
        f"{result.strftime('%Y-%m-%d %H:%M %Z')}"
    )
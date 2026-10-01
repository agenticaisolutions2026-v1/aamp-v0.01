from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import Campaign


now = datetime.now(timezone.utc)

with Session(engine) as session:
    campaigns = session.scalars(
        select(Campaign)
    ).all()

    print(f"\nCurrent UTC time: {now}\n")

    for c in campaigns:
        due = (
            c.next_follow_up_at is not None
            and c.next_follow_up_at <= now
        )

        print(
            f"ID={c.id} | "
            f"status={c.status} | "
            f"category={c.response_category} | "
            f"channel={c.channel} | "
            f"follow_up_count={c.follow_up_count} | "
            f"next_follow_up_at={c.next_follow_up_at} | "
            f"due={due}"
        )
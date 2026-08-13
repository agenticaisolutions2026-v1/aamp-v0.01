# from sqlalchemy import text

# from backend.database.connection import engine


# def test_database_connection():
#     try:
#         with engine.connect() as connection:
#             connection.execute(text("SELECT 1"))

#         print("Database connection successful")

#     except Exception as error:
#         print("Database connection failed")
#         print(error)


# if __name__ == "__main__":
#     test_database_connection()

from datetime import datetime

from backend.database.session import SessionLocal
from backend.models import (
    AgentRun,
    Campaign,
    Contact,
    Organization,
)


def test_database_crud():
    db = SessionLocal()

    try:
        organization = Organization(
            name="Test Organization",
        )

        db.add(organization)
        db.commit()
        db.refresh(organization)

        print(f"Organization inserted: {organization.id}")

        contact = Contact(
            organization_id=organization.id,
            name="Test Contact",
            email="test@example.com",
            phone="9876543210",
        )

        db.add(contact)

        campaign = Campaign(
            organization_id=organization.id,
            name="Test Campaign",
            description="Test campaign for database verification",
            status="draft",
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        print(f"Contact inserted: {contact.id}")
        print(f"Campaign inserted: {campaign.id}")

        agent_run = AgentRun(
            campaign_id=campaign.id,
            agent_name="Test Agent",
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        print(f"Agent run inserted: {agent_run.id}")

        retrieved_organization = db.get(
            Organization,
            organization.id,
        )

        retrieved_campaign = db.get(
            Campaign,
            campaign.id,
        )

        retrieved_agent_run = db.get(
            AgentRun,
            agent_run.id,
        )

        print(
            f"Organization retrieved: "
            f"{retrieved_organization.name}"
        )

        print(
            f"Campaign retrieved: "
            f"{retrieved_campaign.name}"
        )

        print(
            f"Agent run retrieved: "
            f"{retrieved_agent_run.agent_name}"
        )

        print("Database insert and retrieval successful")

    except Exception as error:
        db.rollback()
        print("Database CRUD test failed")
        print(error)

    finally:
        db.close()


if __name__ == "__main__":
    test_database_crud()
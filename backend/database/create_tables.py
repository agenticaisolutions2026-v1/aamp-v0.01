from backend.database.base import Base
from backend.database.connection import engine

from backend.database.models import (
    Organization,
    College,
    Campaign,
    Outreach,
)


Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")
from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
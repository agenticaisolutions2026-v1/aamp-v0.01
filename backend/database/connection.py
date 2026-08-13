import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "aamp_db")

if not DB_PASSWORD:
    raise ValueError("POSTGRES_PASSWORD is not set in the .env file")


DATABASE_URL = (f"postgresql+psycopg://" f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


engine = create_engine(DATABASE_URL,pool_pre_ping=True,)
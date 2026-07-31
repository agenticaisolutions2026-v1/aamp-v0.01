import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env file
load_dotenv()

# Read database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Build connection string
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

try:
    # Create database engine
    engine = create_engine(DATABASE_URL)

    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))

        print("✅ Database connected successfully!")
        print("PostgreSQL Version:")
        print(result.scalar())

except Exception as e:
    print("❌ Database connection failed!")
    print(e)
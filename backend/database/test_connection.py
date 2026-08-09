from sqlalchemy import text

from backend.database.connection import engine


try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("✅ PostgreSQL connection successful!")

except Exception as e:
    print("❌ PostgreSQL connection failed!")
    print(e)
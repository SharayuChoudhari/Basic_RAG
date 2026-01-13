import os
from sqlmodel import create_engine, Session
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Create engine
engine = create_engine(DATABASE_URL)


def get_db_session():
    """
    Dependency function to get a database session.
    This should be used with FastAPI's Depends() to provide database sessions to endpoints.
    """
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """
    Create database tables. This should be called once during application startup.
    """
    from layers.models import SQLModel
    SQLModel.metadata.create_all(bind=engine)
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from typing import Generator
import logging

from app.config.config import settings

logger = logging.getLogger(__name__)

# SQLite requires different connection arguments for threading
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    logger.info("Configuring SQLite database connection.")
else:
    # Use pool settings suited for PostgreSQL in production
    connect_args = {
        # You can add custom connection args here if needed (e.g. sslmode)
    }
    logger.info("Configuring PostgreSQL database connection.")

# Initialize the SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # checks connection validity before querying
)

# Initialize SessionLocal session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models (SQLAlchemy 2.0 standard)
class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    """
    FastAPI dependency that provides a transactional database session.
    Automatically closes the connection when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

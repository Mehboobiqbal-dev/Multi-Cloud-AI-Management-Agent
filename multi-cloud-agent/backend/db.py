import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from core.db import Base
import logging
from core.config import settings
from urllib.parse import urlparse

# Determine driver to set appropriate connect_args
parsed_url = urlparse(settings.DATABASE_URL)
if parsed_url.scheme.startswith("sqlite"):
    # SQLite does not understand TCP-level options
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )
else:
    # Other SQL dialects (e.g., Postgres, MySQL) - keep robust TCP settings
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

def get_db():
    """
    Dependency that creates a new database session for each request
    and closes it after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables defined in the models
    """
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

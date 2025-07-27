import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from models import Base
import logging
from config import settings

# Create engine with more robust connection parameters
engine = create_engine(
    settings.DATABASE_URL,
    # Disable connection pooling to prevent hanging connections
    poolclass=NullPool,
    # Connection timeout and other parameters
    connect_args={
        "connect_timeout": 10,  # 10 seconds connection timeout
        "keepalives": 1,        # Enable TCP keepalives
        "keepalives_idle": 30,  # Keepalive packet sent after 30 seconds of idle time
        "keepalives_interval": 10,  # Retransmit keepalive packet every 10 seconds
        "keepalives_count": 5   # Close connection after 5 failed keepalive attempts
    }
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    # Add additional session configuration if needed
    expire_on_commit=False  # Keep objects usable after session is closed
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

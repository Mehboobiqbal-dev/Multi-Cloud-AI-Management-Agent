import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Remove the database file if it exists
db_file = 'database.db'
db_file_path = os.path.abspath(db_file)
logger.info(f"Attempting to initialize database at: {db_file_path}")
if os.path.exists(db_file_path):
    logger.info(f"Existing database file found: {db_file_path}. Attempting to remove...")
    try:
        os.remove(db_file_path)
        logger.info(f"Database file removed successfully: {db_file_path}")
    except OSError as e:
        logger.error(f"Error removing database file {db_file_path}: {e}")
        # Depending on the error, you might want to exit or handle it differently
else:
    logger.info(f"No existing database file found at: {db_file_path}. Proceeding with creation.")

# Verify file does not exist after attempted removal
if os.path.exists(db_file_path):
    logger.warning(f"Database file still exists after attempted removal: {db_file_path}. This might indicate a permission issue or another process holding the file.")
else:
    logger.info(f"Database file confirmed not to exist after removal attempt: {db_file_path}.")

# Import the necessary modules
from core.db import Base, engine

# Import all models to ensure they're registered with the Base metadata
logger.info("Importing models...")
try:
    # Import models from models.py
    from models import User, CloudCredential, AuditLog, PlanHistory
    logger.info("Models imported successfully")
    
    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables created: {tables}")
    
    # Check if the users table exists
    if 'users' in tables:
        logger.info("'users' table exists in the database")
    else:
        logger.error("'users' table does not exist in the database")
        # Check User model tablename
        logger.info(f"User model tablename: {User.__tablename__}")
        
    # Print all models and their tablenames
    logger.info(f"User.__tablename__: {User.__tablename__}")
    logger.info(f"CloudCredential.__tablename__: {CloudCredential.__tablename__}")
    logger.info(f"AuditLog.__tablename__: {AuditLog.__tablename__}")
    logger.info(f"PlanHistory.__tablename__: {PlanHistory.__tablename__}")
    
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    raise

logger.info("Database initialization completed")
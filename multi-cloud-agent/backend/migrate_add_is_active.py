import os
import sys
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database connection
from core.db import engine

def migrate_add_is_active_column():
    """Add is_active and is_superuser columns to users table if they don't exist"""
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                # Check if is_active column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'is_active'
                """))
                
                if not result.fetchone():
                    logger.info("Adding is_active column to users table...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE
                    """))
                    logger.info("is_active column added successfully")
                else:
                    logger.info("is_active column already exists")
                
                # Check if is_superuser column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'is_superuser'
                """))
                
                if not result.fetchone():
                    logger.info("Adding is_superuser column to users table...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT FALSE
                    """))
                    logger.info("is_superuser column added successfully")
                else:
                    logger.info("is_superuser column already exists")
                
                # Check if created_at column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'created_at'
                """))
                
                if not result.fetchone():
                    logger.info("Adding created_at column to users table...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    """))
                    logger.info("created_at column added successfully")
                else:
                    logger.info("created_at column already exists")
                
                # Check if updated_at column exists
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'updated_at'
                """))
                
                if not result.fetchone():
                    logger.info("Adding updated_at column to users table...")
                    connection.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    """))
                    logger.info("updated_at column added successfully")
                else:
                    logger.info("updated_at column already exists")
                
                # Commit the transaction
                trans.commit()
                logger.info("Migration completed successfully")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database migration...")
    migrate_add_is_active_column()
    logger.info("Database migration completed")
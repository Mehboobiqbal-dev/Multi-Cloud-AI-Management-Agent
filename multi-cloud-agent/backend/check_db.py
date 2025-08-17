from core.db import engine, init_db, Base
from sqlalchemy import inspect
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all models explicitly
from models import User, CloudCredential, AuditLog, PlanHistory, ChatHistory, AgentSession

print('=== Database Diagnostic ===')
print(f'Database URL: {engine.url}')
print(f'Base metadata tables: {list(Base.metadata.tables.keys())}')

# Check existing tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Existing tables: {tables}')

if not tables:
    print('No tables found, initializing database...')
    try:
        # Create tables manually to see what happens
        Base.metadata.create_all(bind=engine)
        print('Tables created via Base.metadata.create_all')
        
        # Check again
        tables = inspector.get_table_names()
        print(f'Tables after manual creation: {tables}')
        
        # Also try init_db function
        init_db()
        tables = inspector.get_table_names()
        print(f'Tables after init_db(): {tables}')
        
    except Exception as e:
        print(f'Error during table creation: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Database already has tables')

# Test a simple query
try:
    from core.db import SessionLocal
    
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f'User count: {user_count}')
    db.close()
    print('Database query test successful')
except Exception as e:
    print(f'Database query test failed: {e}')
    import traceback
    traceback.print_exc()
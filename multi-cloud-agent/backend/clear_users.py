import os
from sqlalchemy import create_engine
from models import User
from db import SessionLocal

# Clear all users
db = SessionLocal()
db.query(User).delete()
db.commit()
print("Users table cleared!")
import os
from sqlalchemy import create_engine
from models import User
from core.db import SessionLocal

def clear_all_users():
    """Function to clear all users from the database"""
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()
        print("Users table cleared!")
    finally:
        db.close()

# This script can be run directly
if __name__ == "__main__":
    clear_all_users()
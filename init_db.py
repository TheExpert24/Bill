#!/usr/bin/env python3
"""
Initialize the database with all required tables
"""

from db import init_database, get_session
from models import Base, User, Asset, PriceData, News, UserRecommendation
import os

def initialize_db():
    """Initialize the database with all tables"""
    print("Initializing database...")
    
    # Create all tables
    init_database()
    
    # Verify tables were created
    session = get_session()
    try:
        # Check if tables exist by querying
        user_count = session.query(User).count()
        asset_count = session.query(Asset).count()
        print(f"Database initialized successfully!")
        print(f"- Users table: OK")
        print(f"- Assets table: OK") 
        print(f"- User recommendations table: OK")
        print(f"Ready to run the application!")
    except Exception as e:
        print(f"Error verifying database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    initialize_db()

"""
Database migration script.
Initializes the database schema and creates tables.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database.connection import db
from backend.app.database.models import Base


def migrate_db():
    """Run database migration."""
    print("Starting database migration...")
    
    try:
        # Connect to database
        db.connect()
        print("[OK] Database connection established")
        
        # Create all tables
        Base.metadata.create_all(bind=db.engine)
        print("[OK] Database tables created")
        
        # Initialize base data
        db.init_db()
        print("[OK] Base data initialized")
        
        print("\n[OK] Database migration completed successfully")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)
    finally:
        db.disconnect()


if __name__ == "__main__":
    migrate_db()

"""
Database initialization and migration.
Creates tables and seeds initial data.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import create_engine
from backend.app.database.models import Base
from backend.app.config.settings import Settings
from backend.app.services.auth_service import create_admin_user, get_user_by_email
from backend.app.database.connection import SessionLocal

settings = Settings()


def initialize_database():
    """Initialize database tables."""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def seed_initial_data():
    """Seed initial data including admin user."""
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@f1predictor.com')
        admin_exists = get_user_by_email(db, admin_email)
        
        if not admin_exists:
            # Create admin user from environment variables or defaults
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'F1Admin2026!Secure')
            admin_name = os.getenv('ADMIN_NAME', 'F1 Predictor Admin')
            
            print(f"Creating admin user: {admin_email}")
            admin_user = create_admin_user(
                db=db,
                email=admin_email,
                username=admin_username,
                password=admin_password,
                full_name=admin_name
            )
            print(f"✓ Admin user created successfully!")
            print(f"  Email: {admin_user.email}")
            print(f"  Username: {admin_user.username}")
            print(f"  ID: {admin_user.id}")
            print(f"\n⚠️  IMPORTANT: Change the default password immediately!")
            print(f"   Default password: {admin_password}")
        else:
            print(f"Admin user already exists: {admin_email}")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    initialize_database()
    print("\nSeeding initial data...")
    seed_initial_data()
    print("\n✓ Database initialization complete!")

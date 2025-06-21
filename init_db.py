import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.append(project_root)

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.db.base import Base, engine, get_db
from app.models.models import User, UserRole
from app.core.security import get_password_hash

def init_db():
    """Initialize the database with required tables and an admin user."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if it doesn't exist
    db = next(get_db())
    try:
        admin_email = "admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        
        if not admin:
            print("Creating admin user...")
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"Admin user created with email: {admin_email} and password: admin123")
        else:
            print("Admin user already exists")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")

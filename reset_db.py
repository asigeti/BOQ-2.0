import os
import sys
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import engine
from app.db.base import Base
# Import all models to ensure they are registered with Base.metadata
from app import models

def reset_database():
    print("Resetting database...")
    try:
        # Drop all tables with CASCADE
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        print("All tables dropped.")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        print("All tables recreated.")

        # Seed default user
        from sqlalchemy.orm import Session
        from app.models.user import User
        from app.core import security
        
        with Session(engine) as session:
            hashed_pwd = security.get_password_hash("password")
            user = User(email="admin@example.com", hashed_password=hashed_pwd, is_active=True, is_superuser=True)
            session.add(user)
            session.commit()
            print("Default user created (ID: 1).")
        
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()

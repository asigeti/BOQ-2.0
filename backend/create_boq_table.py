"""
Script to create the BOQ items table in the database.
Run this once to add the new table: python create_boq_table.py
"""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from app.models import BOQItem
from app.db.base import Base

def create_tables():
    print("Creating boq_items table...")
    try:
        # Create only the BOQItem table
        BOQItem.__table__.create(bind=engine, checkfirst=True)
        print("[OK] boq_items table created successfully!")
    except Exception as e:
        print(f"[ERROR] Error creating table: {e}")
        raise

if __name__ == "__main__":
    create_tables()

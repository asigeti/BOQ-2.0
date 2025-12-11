"""
One-time migration script to add BOQ hierarchy tables.
Run this once to apply the 4-level Israeli BOQ hierarchy schema.
"""
from sqlalchemy import text
from app.db.session import engine

def run_migration():
    print("Running BOQ hierarchy migration...")

    with engine.connect() as conn:
        # ==========================================================================
        # Create boq_sub_document table (Level 1 - תת כתב)
        # ==========================================================================
        print("Creating boq_sub_document table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS boq_sub_document (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
                code VARCHAR(10) NOT NULL,
                name_he VARCHAR(300) NOT NULL,
                name_en VARCHAR(300),
                display_order INTEGER DEFAULT 0,
                description TEXT,
                cached_total FLOAT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_document_id ON boq_sub_document(id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_document_project_id ON boq_sub_document(project_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_document_code ON boq_sub_document(code)"))
        conn.commit()

        # ==========================================================================
        # Create boq_chapter table (Level 2 - פרק)
        # ==========================================================================
        print("Creating boq_chapter table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS boq_chapter (
                id SERIAL PRIMARY KEY,
                sub_document_id INTEGER NOT NULL REFERENCES boq_sub_document(id) ON DELETE CASCADE,
                code VARCHAR(10) NOT NULL,
                full_code VARCHAR(20),
                name_he VARCHAR(300) NOT NULL,
                name_en VARCHAR(300),
                dekel_code VARCHAR(50),
                display_order INTEGER DEFAULT 0,
                description TEXT,
                cached_total FLOAT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_chapter_id ON boq_chapter(id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_chapter_sub_document_id ON boq_chapter(sub_document_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_chapter_code ON boq_chapter(code)"))
        conn.commit()

        # ==========================================================================
        # Create boq_sub_chapter table (Level 3 - תת פרק)
        # ==========================================================================
        print("Creating boq_sub_chapter table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS boq_sub_chapter (
                id SERIAL PRIMARY KEY,
                chapter_id INTEGER NOT NULL REFERENCES boq_chapter(id) ON DELETE CASCADE,
                code VARCHAR(10) NOT NULL,
                full_code VARCHAR(30),
                name_he VARCHAR(300) NOT NULL,
                name_en VARCHAR(300),
                display_order INTEGER DEFAULT 0,
                description TEXT,
                cached_total FLOAT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_chapter_id ON boq_sub_chapter(id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_chapter_chapter_id ON boq_sub_chapter(chapter_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_sub_chapter_code ON boq_sub_chapter(code)"))
        conn.commit()

        # ==========================================================================
        # Add new columns to boq_items for hierarchy support
        # ==========================================================================
        print("Adding columns to boq_items...")

        # Check which columns exist
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'boq_items'
        """))
        existing_columns = {row[0] for row in result}

        # Add missing columns
        if 'sub_chapter_id' not in existing_columns:
            print("  Adding sub_chapter_id...")
            conn.execute(text("ALTER TABLE boq_items ADD COLUMN sub_chapter_id INTEGER REFERENCES boq_sub_chapter(id) ON DELETE SET NULL"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_items_sub_chapter_id ON boq_items(sub_chapter_id)"))
            conn.commit()

        if 'section_code' not in existing_columns:
            print("  Adding section_code...")
            conn.execute(text("ALTER TABLE boq_items ADD COLUMN section_code VARCHAR(20)"))
            conn.commit()

        if 'full_item_code' not in existing_columns:
            print("  Adding full_item_code...")
            conn.execute(text("ALTER TABLE boq_items ADD COLUMN full_item_code VARCHAR(50)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_boq_items_full_item_code ON boq_items(full_item_code)"))
            conn.commit()

        if 'dekel_code' not in existing_columns:
            print("  Adding dekel_code...")
            conn.execute(text("ALTER TABLE boq_items ADD COLUMN dekel_code VARCHAR(50)"))
            conn.commit()

        if 'standard_reference' not in existing_columns:
            print("  Adding standard_reference...")
            conn.execute(text("ALTER TABLE boq_items ADD COLUMN standard_reference VARCHAR(100)"))
            conn.commit()

        # Make legacy columns nullable (if they exist)
        print("Making legacy columns nullable...")
        try:
            conn.execute(text("ALTER TABLE boq_items ALTER COLUMN chapter_code DROP NOT NULL"))
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            conn.execute(text("ALTER TABLE boq_items ALTER COLUMN chapter_name_he DROP NOT NULL"))
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            conn.execute(text("ALTER TABLE boq_items ALTER COLUMN item_code DROP NOT NULL"))
            conn.commit()
        except Exception:
            conn.rollback()

    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()

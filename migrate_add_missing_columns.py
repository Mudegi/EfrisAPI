"""
Migration script to add missing columns to the database
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:kian256@localhost:5432/efris_multitenant")

def run_migration():
    """Add missing columns to companies and products tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add qb_region to companies table
            print("Adding qb_region column to companies...")
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS qb_region VARCHAR(10) DEFAULT 'US'
            """))
            conn.commit()
            print("✓ Added qb_region column")
            
            # Add is_zero_rated to products table
            print("Adding is_zero_rated column to products...")
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS is_zero_rated BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Added is_zero_rated column")
            
            # Add is_exempt to products table
            print("Adding is_exempt column to products...")
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS is_exempt BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Added is_exempt column")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()

#!/usr/bin/env python3
"""
Add qb_region field to companies table for QuickBooks region detection
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db
from database.models import Company
from sqlalchemy import text

def add_qb_region_field():
    """Add qb_region field to companies table"""
    db = next(get_db())
    
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='companies' AND column_name='qb_region'
        """))
        
        if result.fetchone():
            print("✅ qb_region column already exists")
            return
        
        # Add the column
        print("Adding qb_region column to companies table...")
        db.execute(text("""
            ALTER TABLE companies 
            ADD COLUMN qb_region VARCHAR(10) DEFAULT 'US'
        """))
        
        # Update existing companies to have default region
        db.execute(text("""
            UPDATE companies 
            SET qb_region = 'US' 
            WHERE qb_region IS NULL
        """))
        
        db.commit()
        print("✅ Successfully added qb_region column")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding qb_region column: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_qb_region_field()
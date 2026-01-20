"""
Migration script to add EFRIS status tracking columns to purchase_orders table
Run this once to update existing database
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/efris_db')
engine = create_engine(DATABASE_URL)

def migrate():
    """Add EFRIS status columns to purchase_orders table"""
    print("Starting migration: Adding EFRIS status columns to purchase_orders...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'purchase_orders' 
                AND column_name IN ('efris_status', 'efris_sent_at', 'efris_response', 'efris_error')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'efris_status' in existing_columns:
                print("✓ Columns already exist. No migration needed.")
                trans.rollback()
                return
            
            # Add efris_status column
            print("Adding efris_status column...")
            conn.execute(text("""
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS efris_status VARCHAR(50) DEFAULT 'pending'
            """))
            
            # Add efris_sent_at column
            print("Adding efris_sent_at column...")
            conn.execute(text("""
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS efris_sent_at TIMESTAMP WITH TIME ZONE
            """))
            
            # Add efris_response column
            print("Adding efris_response column...")
            conn.execute(text("""
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS efris_response JSON
            """))
            
            # Add efris_error column
            print("Adding efris_error column...")
            conn.execute(text("""
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS efris_error TEXT
            """))
            
            # Update existing records to have 'pending' status
            print("Updating existing records to 'pending' status...")
            conn.execute(text("""
                UPDATE purchase_orders 
                SET efris_status = 'pending' 
                WHERE efris_status IS NULL
            """))
            
            # Commit transaction
            trans.commit()
            print("✓ Migration completed successfully!")
            print("✓ Added columns: efris_status, efris_sent_at, efris_response, efris_error")
            
        except Exception as e:
            trans.rollback()
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

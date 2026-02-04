"""
Add API key columns to companies table for external ERP integration
Run with: py add_api_key_columns.py
"""
from database.connection import engine
from sqlalchemy import text

def add_api_key_columns():
    """Add API key columns to companies table"""
    
    with engine.connect() as conn:
        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='api_key'
            """))
            
            if result.fetchone():
                print("✅ API key columns already exist!")
                return
            
            # Add the columns
            print("Adding api_key column...")
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN api_key VARCHAR(255) UNIQUE
            """))
            
            print("Adding api_secret column...")
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN api_secret VARCHAR(255)
            """))
            
            print("Adding api_enabled column...")
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN api_enabled BOOLEAN DEFAULT TRUE
            """))
            
            print("Adding api_last_used column...")
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN api_last_used TIMESTAMP
            """))
            
            conn.commit()
            
            print("\n✅ API key columns added successfully!")
            print("\nNext step: Generate API keys for existing companies")
            print("Run: py generate_api_keys.py")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_api_key_columns()

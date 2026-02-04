"""
Migration script to add reseller/client columns to database
"""
from database.connection import engine
from sqlalchemy import text

def migrate():
    print("Adding reseller/client columns to database...")
    
    with engine.connect() as conn:
        # Add columns to users table
        columns_to_add = [
            ("phone", "VARCHAR(50)"),
            ("role", "VARCHAR(20) DEFAULT 'reseller'"),
            ("parent_id", "INTEGER"),
            ("subscription_status", "VARCHAR(20) DEFAULT 'trial'"),
            ("subscription_ends", "TIMESTAMP"),
            ("max_clients", "INTEGER DEFAULT 5"),
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'))
                print(f"  ✓ Added users.{col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  - users.{col_name} already exists")
                else:
                    print(f"  ✗ users.{col_name}: {e}")
        
        # Add owner_id to companies table
        try:
            conn.execute(text('ALTER TABLE companies ADD COLUMN owner_id INTEGER'))
            print(f"  ✓ Added companies.owner_id")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print(f"  - companies.owner_id already exists")
            else:
                print(f"  ✗ companies.owner_id: {e}")
        
        conn.commit()
        print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()

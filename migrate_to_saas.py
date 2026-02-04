"""
Migration script to update database schema for SaaS model
Run this ONCE to migrate your existing database
"""
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path is set
try:
    from auth import get_password_hash
except ImportError:
    # Fallback password hashing
    import hashlib
    def get_password_hash(password):
        return hashlib.sha256(password.encode()).hexdigest()

# Database URL
DATABASE_URL = "sqlite:///efris.db"

def migrate_to_saas():
    """Add new tables and columns for SaaS model"""
    engine = create_engine(DATABASE_URL)
    
    print("[MIGRATE] Step 1: Adding subscription-related columns to users table...")
    with engine.connect() as conn:
        try:
            # Add subscription fields to users table
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'trial'
            """))
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN subscription_start_date TEXT
            """))
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN subscription_end_date TEXT
            """))
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN max_companies INTEGER DEFAULT 2
            """))
            conn.commit()
            print("[MIGRATE] [OK] Added subscription columns to users table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"[MIGRATE] [WARN] Subscription columns already exist")
            else:
                print(f"[MIGRATE] [WARN] Error adding subscription columns: {e}")
    
    print("\n[MIGRATE] Step 2: Adding SaaS columns to companies table...")
    with engine.connect() as conn:
        try:
            # Add user_id to companies table (for multi-tenancy)
            conn.execute(text("ALTER TABLE companies ADD COLUMN user_id INTEGER"))
            conn.commit()
            print("[MIGRATE] [OK] Added user_id to companies table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"[MIGRATE] [WARN] user_id column already exists")
            else:
                print(f"[MIGRATE] [WARN] Error: {e}")
    
    with engine.connect() as conn:
        try:
            # Add ERP type and config
            conn.execute(text("ALTER TABLE companies ADD COLUMN erp_type TEXT DEFAULT 'QUICKBOOKS'"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN erp_config TEXT"))
            conn.commit()
            print("[MIGRATE] [OK] Added ERP columns to companies table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"[MIGRATE] [WARN] ERP columns already exist")
            else:
                print(f"[MIGRATE] [WARN] Error: {e}")
    
    print("\n[MIGRATE] Step 3: Creating or updating admin user...")
    with engine.connect() as conn:
        # Check if admin exists
        result = conn.execute(text("SELECT id FROM users WHERE email = 'mudegiemma@gmail.com'"))
        admin_row = result.fetchone()
        
        if not admin_row:
            # Create admin user with trial subscription
            try:
                hashed_pw = get_password_hash("mudegi@256")
                future_date = (datetime.now() + timedelta(days=3650)).isoformat()  # 10 years
                start_date = datetime.now().isoformat()
                
                conn.execute(text("""
                    INSERT INTO users (
                        email, hashed_password, full_name, is_active, is_superuser,
                        subscription_status, subscription_start_date, subscription_end_date, max_companies
                    ) VALUES (
                        'mudegiemma@gmail.com', :password, 'Platform Owner', 1, 1,
                        'ACTIVE', :start_date, :end_date, 999
                    )
                """), {
                    "password": hashed_pw,
                    "start_date": start_date,
                    "end_date": future_date
                })
                conn.commit()
                print("[MIGRATE] [OK] Created admin user (mudegiemma@gmail.com / mudegi@256)")
            except Exception as e:
                print(f"[MIGRATE] [WARN] Error creating admin: {e}")
        else:
            # Update existing admin with subscription info
            try:
                admin_id = admin_row[0]
                future_date = (datetime.now() + timedelta(days=3650)).isoformat()
                start_date = datetime.now().isoformat()
                
                conn.execute(text("""
                    UPDATE users SET
                        subscription_status = 'ACTIVE',
                        subscription_start_date = :start_date,
                        subscription_end_date = :end_date,
                        max_companies = 999
                    WHERE id = :admin_id
                """), {
                    "admin_id": admin_id,
                    "start_date": start_date,
                    "end_date": future_date
                })
                conn.commit()
                print(f"[MIGRATE] [OK] Updated admin user (ID: {admin_id})")
            except Exception as e:
                print(f"[MIGRATE] [WARN] Error updating admin: {e}")
    
    print("\n[MIGRATE] Step 4: Linking existing companies to admin user...")
    with engine.connect() as conn:
        # Get admin ID
        result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@efris.local'"))
        admin_row = result.fetchone()
        
        if admin_row:
            admin_id = admin_row[0]
            
            # Update all companies without user_id to belong to admin
            try:
                result = conn.execute(text("""
                    UPDATE companies SET user_id = :admin_id WHERE user_id IS NULL
                """), {"admin_id": admin_id})
                conn.commit()
                print(f"[MIGRATE] [OK] Linked {result.rowcount} companies to admin")
            except Exception as e:
                print(f"[MIGRATE] [WARN] Error linking companies: {e}")
        else:
            print("[MIGRATE] [WARN] Admin user not found, cannot link companies")
    
    print("\n" + "="*70)
    print("[MIGRATE] [SUCCESS] Migration complete!")
    print("="*70)
    print("\n=== Platform Owner Credentials ===")
    print("Email:    mudegiemma@gmail.com")
    print("Password: mudegi@256")
    print("\n[!] IMPORTANT: Change the password after first login!")
    print("="*70 + "\n")

if __name__ == "__main__":
    migrate_to_saas()


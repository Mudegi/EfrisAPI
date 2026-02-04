"""
Simple script to update admin credentials directly
"""
import sys
sys.path.insert(0, 'd:\\EfrisAPI')

from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/efris_multitenant")
engine = create_engine(DATABASE_URL)

print("\n🔄 Updating admin credentials...")

with engine.connect() as conn:
    # Step 1: Check if mudegiemma@gmail.com exists
    result = conn.execute(text("SELECT id, role FROM users WHERE email = 'mudegiemma@gmail.com'"))
    existing = result.fetchone()
    
    if existing:
        user_id, role = existing
        print(f"   Found existing user with role: {role}")
        
        if role == 'reseller':
            # Delete the reseller account
            conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            conn.commit()
            print(f"   ✅ Deleted reseller account: mudegiemma@gmail.com")
    
    # Step 2: Check if old admin exists
    result = conn.execute(text("SELECT id FROM users WHERE email = 'admin@efris.local'"))
    old_admin = result.fetchone()
    
    if old_admin:
        # Update old admin to new credentials
        hashed_pw = get_password_hash("mudegi@256")
        conn.execute(text("""
            UPDATE users 
            SET email = 'mudegiemma@gmail.com',
                hashed_password = :password,
                full_name = 'Platform Owner',
                role = 'admin'
            WHERE email = 'admin@efris.local'
        """), {"password": hashed_pw})
        conn.commit()
        print("   ✅ Updated admin@efris.local → mudegiemma@gmail.com")
    else:
        # Update existing mudegiemma account to admin if it exists
        result = conn.execute(text("SELECT id FROM users WHERE email = 'mudegiemma@gmail.com'"))
        if result.fetchone():
            hashed_pw = get_password_hash("mudegi@256")
            conn.execute(text("""
                UPDATE users 
                SET hashed_password = :password,
                    full_name = 'Platform Owner',
                    role = 'admin',
                    status = 'active',
                    is_active = true
                WHERE email = 'mudegiemma@gmail.com'
            """), {"password": hashed_pw})
            conn.commit()
            print("   ✅ Updated mudegiemma@gmail.com to admin role")
        else:
            # Create new admin
            hashed_pw = get_password_hash("mudegi@256")
            conn.execute(text("""
                INSERT INTO users (
                    email, hashed_password, full_name, role, 
                    status, is_active, subscription_status
                ) VALUES (
                    'mudegiemma@gmail.com', :password, 'Platform Owner', 'admin',
                    'active', true, 'active'
                )
            """), {"password": hashed_pw})
            conn.commit()
            print("   ✅ Created new admin: mudegiemma@gmail.com")

print("\n" + "="*60)
print("✅ CREDENTIALS UPDATED")
print("="*60)
print("\n🔑 New Login Credentials:")
print("   Email:    mudegiemma@gmail.com")
print("   Password: mudegi@256")
print("   URL:      http://127.0.0.1:8001/login")
print("\n" + "="*60 + "\n")

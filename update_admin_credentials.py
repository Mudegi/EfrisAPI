"""
Update admin credentials and remove any existing reseller with the new email
"""
from database.connection import engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def update_credentials():
    print("\n🔄 Updating admin credentials...")
    
    with engine.connect() as conn:
        # Step 1: Check if mudegiemma@gmail.com exists as a reseller
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
            # Create new admin if neither exists
            result = conn.execute(text("SELECT id FROM users WHERE email = 'mudegiemma@gmail.com'"))
            if not result.fetchone():
                hashed_pw = get_password_hash("mudegi@256")
                conn.execute(text("""
                    INSERT INTO users (
                        email, hashed_password, full_name, role, 
                        status, is_active, subscription_status
                    ) VALUES (
                        'mudegiemma@gmail.com', :password, 'Platform Owner', 'admin',
                        'active', 1, 'active'
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

if __name__ == "__main__":
    update_credentials()

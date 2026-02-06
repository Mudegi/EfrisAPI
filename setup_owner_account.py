"""
Setup Owner Account for EFRIS Platform
Creates the platform owner account that can manage resellers and direct clients
"""
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def setup_owner_account(reset_password=False):
    """Create or update the platform owner account"""
    db = SessionLocal()
    
    try:
        # Owner credentials
        owner_email = "owner@efrisplatform.com"
        owner_password = "OwnerSecure2026!"
        owner_name = "Platform Owner"
        
        # Check if owner exists
        existing_owner = db.query(User).filter(User.email == owner_email).first()
        
        if existing_owner:
            print(f"[INFO] Owner account already exists")
            print(f"       User ID: {existing_owner.id}")
            print(f"       Email: {owner_email}")
            
            # Update to ensure it's an owner
            if reset_password:
                print(f"[INFO] Resetting password to default...")
                existing_owner.hashed_password = get_password_hash(owner_password)
                print(f"[SUCCESS] Password reset!")
            
            existing_owner.role = 'owner'
            existing_owner.is_active = True
            existing_owner.status = 'active'
            db.commit()
            print(f"[SUCCESS] Owner account verified and updated!")
        else:
            # Create new owner account
            print(f"[INFO] Creating new owner account...")
            
            owner_user = User(
                email=owner_email,
                hashed_password=get_password_hash(owner_password),
                full_name=owner_name,
                role='owner',
                status='active',
                is_active=True,
                subscription_status='active',
                subscription_ends=datetime.utcnow() + timedelta(days=3650)  # 10 years
            )
            
            db.add(owner_user)
            db.commit()
            db.refresh(owner_user)
            
            print(f"[SUCCESS] Owner account created successfully!")
        
        print("\n" + "="*60)
        print("PLATFORM OWNER CREDENTIALS")
        print("="*60)
        print(f"Email:    {owner_email}")
        print(f"Password: {owner_password}")
        print(f"Login:    http://localhost:8001/login")
        print(f"Portal:   http://localhost:8001/owner")
        print("="*60)
        print("\nIMPORTANT: Save these credentials securely!")
        print("Change the password after first login.\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to create owner account: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EFRIS PLATFORM - OWNER ACCOUNT SETUP")
    print("="*60 + "\n")
    
    # Check for command-line arguments
    import sys
    reset = '--reset' in sys.argv or '-r' in sys.argv
    
    setup_owner_account(reset_password=reset)

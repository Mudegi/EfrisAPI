"""
Reset password for existing client
"""
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def reset_client_password():
    db = SessionLocal()
    
    try:
        # Find the client
        client = db.query(User).filter(
            User.email == 'client@wandera.com'
        ).first()
        
        if not client:
            print("❌ Client not found")
            return
        
        # Set new password
        new_password = "Client2026!"
        client.hashed_password = get_password_hash(new_password)
        
        db.commit()
        
        print("\n" + "="*70)
        print("CLIENT PASSWORD RESET SUCCESSFUL")
        print("="*70)
        print(f"\nClient Name:  {client.full_name}")
        print(f"Email:        {client.email}")
        print(f"New Password: {new_password}")
        print(f"\nLogin URL:    http://localhost:8001/client/login")
        print("\n" + "="*70)
        print("\n✅ Client can now login with these credentials!\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_client_password()

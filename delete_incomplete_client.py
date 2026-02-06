"""
Delete incomplete client user to allow re-approval
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

email = "taibu@gmail.com"

print(f"Deleting incomplete client: {email}")

try:
    # Check if user exists
    check_query = text("SELECT id, full_name, role FROM users WHERE email = :email")
    result = db.execute(check_query, {"email": email})
    user = result.fetchone()
    
    if user:
        print(f"Found user: ID={user[0]}, Name={user[1]}, Role={user[2]}")
        
        # Delete related records first
        print("Deleting CompanyUser records...")
        db.execute(text("DELETE FROM company_users WHERE user_id = :user_id"), {"user_id": user[0]})
        
        print("Deleting user...")
        db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user[0]})
        
        db.commit()
        print(f"✅ Successfully deleted user {email}")
    else:
        print(f"User {email} not found")
        
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()

print("\n✅ Cleanup complete! You can now re-approve the referral.")

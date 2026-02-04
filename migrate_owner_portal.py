"""
Migration Script: Add Owner Portal Features
- Adds 'status' column to users table for activation workflow
- Creates activity_logs table for tracking EFRIS operations
- Creates owner account with role='owner'
"""
from database.connection import SessionLocal, engine
from database.models import Base, User, ActivityLog
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def migrate():
    db = SessionLocal()
    
    print("🔄 Starting owner portal migration...\n")
    
    try:
        # Step 1: Add status column to users
        print("📋 Adding 'status' column to users table...")
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
            db.commit()
            print("   ✓ Added users.status")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("   ⚠ users.status already exists, skipping")
                db.rollback()
            else:
                raise
        
        # Step 2: Create activity_logs table
        print("\n📋 Creating activity_logs table...")
        try:
            Base.metadata.tables['activity_logs'].create(engine)
            print("   ✓ Created activity_logs table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ activity_logs table already exists, skipping")
            else:
                raise
        
        # Step 3: Update existing users to have active status
        print("\n📋 Updating existing users status to 'active'...")
        db.execute(text("UPDATE users SET status = 'active' WHERE status IS NULL OR status = ''"))
        db.commit()
        print("   ✓ Updated existing users")
        
        # Step 4: Check if owner account exists
        print("\n📋 Checking for owner account...")
        owner = db.query(User).filter(User.role == 'owner').first()
        
        if not owner:
            print("   Creating owner account...")
            owner = User(
                email="owner@efrisplatform.com",
                hashed_password=get_password_hash("OwnerPass123!"),
                full_name="Platform Owner",
                phone="+256700000000",
                role="owner",
                status="active",
                is_active=True,
                is_superuser=True
            )
            db.add(owner)
            db.commit()
            print("   ✓ Owner account created")
            print("\n   📧 Email: owner@efrisplatform.com")
            print("   🔑 Password: OwnerPass123!")
            print("   🌐 URL: http://localhost:8001/owner")
        else:
            print("   ⚠ Owner account already exists")
            print(f"   📧 Email: {owner.email}")
        
        print("\n✅ Migration complete!")
        print("\n📊 Summary:")
        print("   - Status column added to users")
        print("   - Activity logs table created")
        print("   - Owner account ready")
        print("\n🚀 Next steps:")
        print("   1. Restart the server: py api_multitenant.py")
        print("   2. Login as owner: http://localhost:8001/owner")
        print("   3. Approve pending clients from the dashboard")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

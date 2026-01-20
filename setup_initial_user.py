"""
Manual user and company setup
"""
from database.connection import SessionLocal
from database.models import User, Company, CompanyUser
from auth.security import get_password_hash

def create_initial_setup():
    """Create initial admin user and company"""
    db = SessionLocal()
    try:
        # Create admin user
        print("Creating admin user...")
        admin_user = User(
            email="admin@wandera.com",
            hashed_password=get_password_hash("Admin2026!"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✓ Admin user created: {admin_user.email} (ID: {admin_user.id})")
        
        # Create company
        print("\nCreating company...")
        company = Company(
            name="Wandera EFRIS",
            tin="1014409555",
            device_no="1014409555_02",
            efris_cert_path="keys/wandera.pfx",
            efris_cert_password="123456",
            efris_test_mode=True,
            is_active=True
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✓ Company created: {company.name} (ID: {company.id}, TIN: {company.tin})")
        
        # Link user to company as admin
        print("\nLinking user to company...")
        company_user = CompanyUser(
            user_id=admin_user.id,
            company_id=company.id,
            role="admin"
        )
        db.add(company_user)
        db.commit()
        print(f"✓ User linked to company as admin")
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print(f"\nLogin Credentials:")
        print(f"  Email: {admin_user.email}")
        print(f"  Password: Admin2026!")
        print(f"\nCompany:")
        print(f"  Name: {company.name}")
        print(f"  TIN: {company.tin}")
        print(f"  ID: {company.id}")
        
        return admin_user, company
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_setup()

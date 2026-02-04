"""
Migration Script: Add ERP Connection Fields
- Adds Xero, Zoho, Custom API fields to companies table
- Adds erp_type, erp_connected, erp_last_sync fields for tracking connection status
"""
from database.connection import SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    
    print("🔄 Starting ERP connection fields migration...\n")
    
    try:
        # List of new columns to add
        columns = [
            ("xero_tenant_id", "VARCHAR(100)"),
            ("xero_access_token", "TEXT"),
            ("xero_refresh_token", "TEXT"),
            ("xero_token_expires", "TIMESTAMP"),
            ("zoho_organization_id", "VARCHAR(100)"),
            ("zoho_access_token", "TEXT"),
            ("zoho_refresh_token", "TEXT"),
            ("zoho_token_expires", "TIMESTAMP"),
            ("custom_api_url", "VARCHAR(500)"),
            ("custom_api_key", "TEXT"),
            ("custom_api_secret", "TEXT"),
            ("erp_type", "VARCHAR(50)"),
            ("erp_connected", "BOOLEAN DEFAULT FALSE"),
            ("erp_last_sync", "TIMESTAMP"),
        ]
        
        print("📋 Adding ERP connection fields to companies table...")
        
        for col_name, col_type in columns:
            try:
                db.execute(text(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}"))
                db.commit()
                print(f"   ✓ Added companies.{col_name}")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ⚠ companies.{col_name} already exists, skipping")
                    db.rollback()
                else:
                    raise
        
        print("\n✅ Migration complete!")
        print("\n📊 Summary:")
        print("   - Xero connection fields added")
        print("   - Zoho Books connection fields added")
        print("   - Custom API fields added")
        print("   - ERP status tracking fields added")
        print("\n🚀 Next steps:")
        print("   1. Restart the server: py api_multitenant.py")
        print("   2. Login to client dashboard")
        print("   3. Click 'Connect Now' to connect QuickBooks/Xero/Zoho")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

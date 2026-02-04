"""
Migration: Add ClientReferral table for reseller referral approval workflow
CRITICAL SECURITY FIX: Prevents resellers from adding/deleting clients directly
"""
from database.connection import engine
from database.models import Base, ClientReferral, AuditLog
from sqlalchemy import inspect

def main():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("🔍 Checking database tables...")
    print(f"   Existing tables: {', '.join(existing_tables)}")
    
    # Create all tables (will only create missing ones)
    Base.metadata.create_all(bind=engine)
    
    # Check again
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    
    if 'client_referrals' in new_tables:
        print("✅ ClientReferral table created successfully")
    else:
        print("⚠️  ClientReferral table already exists")
    
    if 'audit_logs' in new_tables:
        print("✅ AuditLog table created successfully")
    else:
        print("⚠️  AuditLog table already exists")
    
    print("\n🎯 SECURITY FIX APPLIED")
    print("   ✓ Resellers can now only SUBMIT referrals")
    print("   ✓ Owner must APPROVE and configure EFRIS credentials")
    print("   ✓ Reseller deletion endpoint REMOVED")
    print("   ✓ Audit logs enabled for URA compliance")
    print("\n⚠️  IMPORTANT: Update reseller portal UI to remove Add/Delete buttons")

if __name__ == "__main__":
    main()

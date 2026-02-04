"""
Generate API keys for all companies that don't have one yet
Run with: py generate_api_keys.py
"""
from database.connection import SessionLocal
from database.models import Company
import secrets
import hashlib

def generate_api_key():
    """Generate a secure API key"""
    random_string = secrets.token_urlsafe(32)
    return f"efris_{random_string}"

def generate_api_secret():
    """Generate a secure API secret"""
    return secrets.token_urlsafe(48)

def generate_keys_for_companies():
    """Generate API keys for all companies without one"""
    db = SessionLocal()
    
    try:
        # Get all companies
        companies = db.query(Company).all()
        
        if not companies:
            print("❌ No companies found in database!")
            print("Create a company first using the admin interface or API.")
            return
        
        print(f"\n📋 Found {len(companies)} companies")
        print("=" * 80)
        
        updated_count = 0
        
        for company in companies:
            if not company.api_key:
                # Generate new API key and secret
                api_key = generate_api_key()
                api_secret = generate_api_secret()
                
                company.api_key = api_key
                company.api_secret = api_secret
                company.api_enabled = True
                
                print(f"\n✅ Generated API key for: {company.name}")
                print(f"   TIN: {company.tin}")
                print(f"   API Key: {api_key}")
                print(f"   API Secret: {api_secret[:20]}...")
                print("-" * 80)
                
                updated_count += 1
            else:
                print(f"\n⏭️  Skipped (already has key): {company.name}")
                print(f"   TIN: {company.tin}")
                print(f"   API Key: {company.api_key}")
                print("-" * 80)
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Generated API keys for {updated_count} companies!")
        else:
            print(f"\n✅ All companies already have API keys!")
        
        print("\n📋 Summary of ALL API Keys:")
        print("=" * 80)
        
        # Refresh to get latest data
        companies = db.query(Company).all()
        for company in companies:
            print(f"\nCompany: {company.name}")
            print(f"TIN: {company.tin}")
            print(f"API Key: {company.api_key}")
            print(f"Enabled: {company.api_enabled}")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_keys_for_companies()

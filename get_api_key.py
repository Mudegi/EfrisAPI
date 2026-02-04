"""
Quick script to get API key for a company
"""
from database.connection import SessionLocal
from database.models import Company

def get_company_api_key():
    db = SessionLocal()
    
    # List all companies
    companies = db.query(Company).all()
    
    if not companies:
        print("❌ No companies found in database!")
        print("You need to create a company first using the admin interface.")
        return
    
    print("\n📋 Companies in database:")
    print("-" * 80)
    for company in companies:
        print(f"ID: {company.id}")
        print(f"Name: {company.company_name}")
        print(f"TIN: {company.tin}")
        print(f"API Key: {company.api_key}")
        print(f"API Enabled: {company.api_enabled}")
        print(f"Last Used: {company.api_last_used}")
        print("-" * 80)
    
    db.close()

if __name__ == "__main__":
    get_company_api_key()

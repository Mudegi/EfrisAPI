"""View API credentials for all companies or specific company"""
import sys
from database.connection import SessionLocal
from database.models import Company

db = SessionLocal()

if len(sys.argv) > 1:
    # Show specific company by TIN or name
    search_term = sys.argv[1]
    companies = db.query(Company).filter(
        (Company.tin.like(f'%{search_term}%')) | 
        (Company.name.like(f'%{search_term}%'))
    ).all()
    
    if not companies:
        print(f"❌ No company found matching '{search_term}'")
        sys.exit(1)
else:
    # Show all companies
    companies = db.query(Company).all()

print("\n" + "=" * 100)
print("API CREDENTIALS FOR CUSTOM ERP INTEGRATION")
print("=" * 100 + "\n")

for company in companies:
    print(f"🏢 Company: {company.name}")
    print(f"   TIN: {company.tin}")
    print(f"   ERP Type: {company.erp_type or 'none'}")
    print(f"   API Enabled: {'✅ Yes' if company.api_enabled else '❌ No'}")
    
    if company.api_key:
        print(f"\n   🔑 API CREDENTIALS:")
        print(f"   API Key:     {company.api_key}")
        print(f"   API Secret:  {company.api_secret or '(not set)'}")
        print(f"   Endpoint:    http://localhost:8001/api/external/efris")
        
        if company.api_last_used:
            print(f"   Last Used:   {company.api_last_used}")
        else:
            print(f"   Last Used:   Never")
    else:
        print(f"\n   ⚠️  NO API CREDENTIALS GENERATED")
        print(f"   Run: py generate_api_credentials.py")
    
    print("\n" + "-" * 100 + "\n")

print(f"Total companies: {len(companies)}")
print(f"\n📚 Integration Guide: DEVELOPER_PACKAGE folder")
print(f"💡 Usage: py view_api_credentials.py [TIN or company name]\n")

db.close()

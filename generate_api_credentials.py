"""Generate API credentials for companies that don't have them"""
import secrets
from database.connection import SessionLocal
from database.models import Company

db = SessionLocal()

# Find companies without API keys
companies_without_keys = db.query(Company).filter(
    (Company.api_key == None) | (Company.api_key == '')
).all()

print(f"\n=== Found {len(companies_without_keys)} companies without API keys ===\n")

for company in companies_without_keys:
    # Generate credentials
    api_key = f"efris_{secrets.token_urlsafe(32)}"
    api_secret = secrets.token_urlsafe(32)
    
    # Update company
    company.api_key = api_key
    company.api_secret = api_secret
    company.api_enabled = True
    
    print(f"Company: {company.name} (TIN: {company.tin})")
    print(f"  API Key: {api_key}")
    print(f"  API Secret: {api_secret}")
    print(f"  ERP Type: {company.erp_type or 'none'}")
    print()

# Commit changes
db.commit()
print(f"✅ Generated API credentials for {len(companies_without_keys)} companies")
print("\n💡 Give these credentials to the custom ERP developers")
print("📚 Documentation: DEVELOPER_PACKAGE folder\n")

db.close()

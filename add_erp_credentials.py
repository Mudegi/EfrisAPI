"""
Add ERP client credentials columns to companies table
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# SQL to add missing ERP credential columns
sql_statements = [
    # QuickBooks client credentials
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS qb_client_id VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS qb_client_secret TEXT;",
    
    # Xero client credentials
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS xero_client_id VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS xero_client_secret TEXT;",
    
    # Zoho client credentials
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS zoho_client_id VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS zoho_client_secret TEXT;",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS zoho_org_id VARCHAR(100);",
    
    # Sage credentials
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS sage_company_id VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS sage_api_key TEXT;",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS sage_api_secret TEXT;",
    
    # Odoo credentials
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS odoo_url VARCHAR(500);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS odoo_db VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS odoo_username VARCHAR(255);",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS odoo_password TEXT;",
    
    # Custom API fields (already exist as custom_api_url, custom_api_key, custom_api_secret)
]

print("Adding ERP credential columns to companies table...")
with engine.connect() as conn:
    for sql in sql_statements:
        try:
            conn.execute(text(sql))
            print(f"✓ Executed: {sql[:80]}...")
        except Exception as e:
            print(f"✗ Error: {sql[:80]}... - {e}")
    conn.commit()

print("\n✅ Migration complete!")
print("ERP credential columns added successfully.")

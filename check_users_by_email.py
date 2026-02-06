"""
Check users and companies by email/TIN to debug conflicts
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

print("=" * 80)
print("ALL USERS IN DATABASE:")
print("=" * 80)

users_query = text("""
    SELECT id, email, full_name, role, is_active, created_at 
    FROM users 
    ORDER BY created_at DESC
""")

result = db.execute(users_query)
users = result.fetchall()

for user in users:
    print(f"ID: {user[0]}, Email: {user[1]}, Name: {user[2]}, Role: {user[3]}, Active: {user[4]}, Created: {user[5]}")

print("\n" + "=" * 80)
print("ALL COMPANIES IN DATABASE:")
print("=" * 80)

companies_query = text("""
    SELECT id, name, tin, owner_id, is_active, created_at 
    FROM companies 
    ORDER BY created_at DESC
""")

result = db.execute(companies_query)
companies = result.fetchall()

for company in companies:
    print(f"ID: {company[0]}, Name: {company[1]}, TIN: {company[2]}, Owner: {company[3]}, Active: {company[4]}, Created: {company[5]}")

print("\n" + "=" * 80)
print("ALL CLIENT REFERRALS:")
print("=" * 80)

referrals_query = text("""
    SELECT id, company_name, client_email, client_name, tin, status, reseller_id, created_at 
    FROM client_referrals 
    ORDER BY created_at DESC
""")

result = db.execute(referrals_query)
referrals = result.fetchall()

for ref in referrals:
    print(f"ID: {ref[0]}, Company: {ref[1]}, Email: {ref[2]}, Name: {ref[3]}, TIN: {ref[4]}, Status: {ref[5]}, Reseller: {ref[6]}, Created: {ref[7]}")

db.close()

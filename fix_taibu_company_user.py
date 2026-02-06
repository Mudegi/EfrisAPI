"""Create missing CompanyUser record for taibu@gmail.com"""
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host="localhost",
    database="efris_multitenant",
    user="postgres",
    password="kian256"
)

cur = conn.cursor()

# Get User
cur.execute("SELECT id, email, role FROM users WHERE email = 'taibu@gmail.com'")
user = cur.fetchone()
if not user:
    print("❌ User not found!")
    exit()

user_id = user[0]
print(f"✓ Found User: ID {user_id}, Email: {user[1]}, Role: {user[2]}")

# Get Company
cur.execute("SELECT id, name, tin FROM companies WHERE name = 'Taibu Investments'")
company = cur.fetchone()
if not company:
    print("❌ Company not found!")
    exit()

company_id = company[0]
print(f"✓ Found Company: ID {company_id}, Name: {company[1]}, TIN: {company[2]}")

# Check if CompanyUser already exists
cur.execute("""
    SELECT id FROM company_users 
    WHERE user_id = %s AND company_id = %s
""", (user_id, company_id))
existing = cur.fetchone()

if existing:
    print(f"✓ CompanyUser record already exists: ID {existing[0]}")
else:
    # Create CompanyUser record
    cur.execute("""
        INSERT INTO company_users (user_id, company_id, role, created_at)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (user_id, company_id, 'admin', datetime.utcnow()))
    
    new_id = cur.fetchone()[0]
    conn.commit()
    print(f"✅ Created CompanyUser record: ID {new_id}")
    print(f"   User ID: {user_id} (taibu@gmail.com)")
    print(f"   Company ID: {company_id} (Taibu Investments)")
    print(f"   Role: admin")

cur.close()
conn.close()

print("\n✅ Fix complete! taibu@gmail.com can now access Taibu Investments company.")

"""Check CompanyUser records for taibu@gmail.com"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="efris_multitenant",
    user="postgres",
    password="kian256"
)

cur = conn.cursor()

# Check User
cur.execute("SELECT id, email, role FROM users WHERE email = 'taibu@gmail.com'")
user = cur.fetchone()
print("\n=== USER ===")
if user:
    print(f"ID: {user[0]}, Email: {user[1]}, Role: {user[2]}")
else:
    print("User not found!")
    exit()

user_id = user[0]

# Check Company
cur.execute("SELECT id, name, tin FROM companies WHERE name = 'Taibu Investments'")
company = cur.fetchone()
print("\n=== COMPANY ===")
if company:
    print(f"ID: {company[0]}, Name: {company[1]}, TIN: {company[2]}")
else:
    print("Company not found!")

# Check CompanyUser
cur.execute("""
    SELECT id, user_id, company_id, role, created_at 
    FROM company_users 
    WHERE user_id = %s
""", (user_id,))
company_users = cur.fetchall()

print("\n=== COMPANY_USERS ===")
if company_users:
    for cu in company_users:
        print(f"ID: {cu[0]}, UserID: {cu[1]}, CompanyID: {cu[2]}, Role: {cu[3]}, Created: {cu[4]}")
else:
    print("No CompanyUser records found!")
    print(f"\n❌ This is the problem! User ID {user_id} has no CompanyUser records.")
    print("The client was created but not linked to their company.")

# Check all CompanyUser records
cur.execute("SELECT id, user_id, company_id, role FROM company_users ORDER BY id")
all_cu = cur.fetchall()
print(f"\n=== ALL COMPANY_USERS ({len(all_cu)} records) ===")
for cu in all_cu[:10]:  # Show first 10
    print(f"ID: {cu[0]}, UserID: {cu[1]}, CompanyID: {cu[2]}, Role: {cu[3]}")

cur.close()
conn.close()

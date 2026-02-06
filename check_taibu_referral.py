"""Check the referral status for Taibu"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="efris_multitenant",
    user="postgres",
    password="kian256"
)

cur = conn.cursor()

cur.execute("""
    SELECT id, reseller_id, client_email, company_name, tin, status, 
           created_client_id, created_company_id, reviewed_by, reviewed_at, created_at
    FROM client_referrals
    WHERE client_email = 'taibu@gmail.com'
    ORDER BY id DESC
""")

referrals = cur.fetchall()

print("\n=== CLIENT REFERRALS FOR taibu@gmail.com ===")
for ref in referrals:
    print(f"\nID: {ref[0]}")
    print(f"Reseller ID: {ref[1]}")
    print(f"Email: {ref[2]}")
    print(f"Company: {ref[3]}")
    print(f"TIN: {ref[4]}")
    print(f"Status: {ref[5]}")
    print(f"Created Client ID: {ref[6]}")
    print(f"Created Company ID: {ref[7]}")
    print(f"Reviewed By: {ref[8]}")
    print(f"Reviewed At: {ref[9]}")
    print(f"Created At: {ref[10]}")

cur.close()
conn.close()

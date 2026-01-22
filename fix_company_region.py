"""
Fix company region to UK_SANDBOX
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('efris.db')
cursor = conn.cursor()

# Update company 1 to UK_SANDBOX
cursor.execute("UPDATE companies SET qb_region = 'UK_SANDBOX' WHERE id = 1")
conn.commit()

# Verify
cursor.execute("SELECT id, name, qb_region FROM companies WHERE id = 1")
result = cursor.fetchone()
print(f"Updated company: ID={result[0]}, Name={result[1]}, Region={result[2]}")

conn.close()
print("✓ Company region updated to UK_SANDBOX")

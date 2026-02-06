"""
Update referral status to approved since client was already created
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

referral_id = 1
print(f"Updating referral {referral_id} status to 'approved'...")

try:
    # Update referral status
    update_query = text("""
        UPDATE client_referrals 
        SET status = 'approved',
            reviewed_at = NOW(),
            reviewed_by = (SELECT id FROM users WHERE role = 'owner' LIMIT 1),
            created_client_id = (SELECT id FROM users WHERE email = 'taibu@gmail.com'),
            created_company_id = (SELECT id FROM companies WHERE tin = '1014409555')
        WHERE id = :referral_id
        RETURNING id, status, created_client_id, created_company_id
    """)
    
    result = db.execute(update_query, {"referral_id": referral_id})
    updated = result.fetchone()
    
    if updated:
        db.commit()
        print(f"✅ Referral {updated[0]} updated successfully!")
        print(f"   Status: {updated[1]}")
        print(f"   Client ID: {updated[2]}")
        print(f"   Company ID: {updated[3]}")
    else:
        print("❌ Referral not found")
        
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()

print("\n✅ Done! Refresh the owner portal to see the updated status.")

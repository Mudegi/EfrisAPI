"""
Find all existing client accounts and their details
"""
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from database.connection import SessionLocal
from database.models import User, Company, CompanyUser

db = SessionLocal()

try:
    # Find all clients
    clients = db.query(User).filter(User.role == 'client').all()
    
    print("\n" + "="*70)
    print("EXISTING CLIENT ACCOUNTS")
    print("="*70)
    
    if not clients:
        print("\n❌ No clients found in the database.")
        print("\nTo create a client:")
        print("  1. Login as owner at: http://localhost:8001/login")
        print("  2. Go to owner portal and click 'Add Client'")
        print("  3. Or have a reseller create a referral for you to approve")
    else:
        for i, client in enumerate(clients, 1):
            print(f"\n{'─'*70}")
            print(f"CLIENT #{i}")
            print(f"{'─'*70}")
            print(f"  User ID:      {client.id}")
            print(f"  Full Name:    {client.full_name}")
            print(f"  Email:        {client.email}")
            print(f"  Phone:        {client.phone or 'N/A'}")
            print(f"  Status:       {client.status}")
            print(f"  Active:       {'Yes' if client.is_active else 'No'}")
            print(f"  Created:      {client.created_at}")
            
            # Find associated company
            company_user = db.query(CompanyUser).filter(
                CompanyUser.user_id == client.id
            ).first()
            
            if company_user:
                company = db.query(Company).filter(
                    Company.id == company_user.company_id
                ).first()
                if company:
                    print(f"\n  Company:      {company.name}")
                    print(f"  TIN:          {company.tin}")
                    print(f"  Device No:    {company.device_no}")
                    print(f"  Test Mode:    {'Yes' if company.efris_test_mode else 'No'}")
            
            print(f"\n  ⚠️  PASSWORD: Cannot retrieve (hashed)")
            print(f"  📱 Login URL: http://localhost:8001/client/login")
            
        print(f"\n{'='*70}")
        print(f"Total Clients: {len(clients)}")
        print(f"{'='*70}")
        
        print("\n💡 TIP: To reset a client password, create a script or")
        print("   update it through the owner portal (if feature exists)")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    db.close()

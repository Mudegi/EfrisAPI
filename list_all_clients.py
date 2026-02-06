"""
List all clients in the system
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
    
    if not clients:
        print("❌ No clients found")
    else:
        print("\n" + "="*70)
        print("ALL CLIENTS IN SYSTEM")
        print("="*70)
        for client in clients:
            companies = db.query(Company).filter(Company.owner_id == client.id).all()
            print(f"\nClient ID: {client.id}")
            print(f"Email: {client.email}")
            print(f"Name: {client.full_name}")
            print(f"Status: {client.status}")
            print(f"Companies: {len(companies)}")
            if companies:
                for company in companies:
                    print(f"  - {company.name} (TIN: {company.tin})")
            print("-" * 70)
    
finally:
    db.close()

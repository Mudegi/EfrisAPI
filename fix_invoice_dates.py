"""Re-import invoices to populate transaction dates"""
from database.connection import get_db
from database.models import Invoice
from datetime import datetime
import json

db = next(get_db())

print("=" * 80)
print("UPDATING INVOICE DATES FROM QB DATA")
print("=" * 80)

invoices = db.query(Invoice).filter(Invoice.company_id == 1).all()
updated_count = 0

for inv in invoices:
    if inv.qb_data and inv.qb_txn_date is None:
        txn_date_str = inv.qb_data.get('TxnDate')
        if txn_date_str:
            try:
                inv.qb_txn_date = datetime.strptime(txn_date_str, '%Y-%m-%d')
                updated_count += 1
                print(f"✓ Updated invoice {inv.qb_doc_number}: {txn_date_str}")
            except Exception as e:
                print(f"✗ Failed to parse date for invoice {inv.qb_doc_number}: {e}")

db.commit()

print("=" * 80)
print(f"✓ Updated {updated_count} invoices with transaction dates")
print("=" * 80)

# Show sorted results
print("\nINVOICES (now sorted by qb_txn_date DESC):")
print("-" * 80)
sorted_invoices = db.query(Invoice).filter(Invoice.company_id == 1).order_by(Invoice.qb_txn_date.desc()).limit(15).all()
for i, inv in enumerate(sorted_invoices, 1):
    print(f"{i:2}. Doc={inv.qb_doc_number:8}, Date={inv.qb_txn_date}, Customer={inv.qb_customer_name}")

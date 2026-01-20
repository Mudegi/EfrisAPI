"""Direct database check for sorting"""
from database.connection import get_db
from database.models import Invoice, Product, EFRISGood, PurchaseOrder
from sqlalchemy import desc

db = next(get_db())

print("=" * 80)
print("DATABASE SORTING TEST")
print("=" * 80)

# Test invoices sorting
print("\n1. INVOICES (sorted by qb_txn_date DESC)")
print("-" * 80)
invoices = db.query(Invoice).filter(Invoice.company_id == 1).order_by(desc(Invoice.qb_txn_date)).limit(10).all()
for i, inv in enumerate(invoices, 1):
    print(f"{i:2}. ID={inv.id:3}, Doc={inv.qb_doc_number:8}, TxnDate={inv.qb_txn_date}, Customer={inv.qb_customer_name}")

# Test products sorting
print("\n2. PRODUCTS (sorted by updated_at DESC)")
print("-" * 80)
products = db.query(Product).filter(Product.company_id == 1).order_by(desc(Product.updated_at)).limit(10).all()
for i, p in enumerate(products, 1):
    updated = p.updated_at.strftime('%Y-%m-%d %H:%M:%S') if p.updated_at else 'None'
    print(f"{i:2}. ID={p.id:3}, Name={p.qb_name[:30]:30}, Updated={updated}")

# Test EFRIS goods sorting
print("\n3. EFRIS GOODS (sorted by updated_at DESC)")
print("-" * 80)
goods = db.query(EFRISGood).filter(EFRISGood.company_id == 1).order_by(desc(EFRISGood.updated_at)).limit(10).all()
for i, g in enumerate(goods, 1):
    updated = g.updated_at.strftime('%Y-%m-%d %H:%M:%S') if g.updated_at else 'None'
    print(f"{i:2}. ID={g.id:3}, Code={g.goods_code[:20]:20}, Updated={updated}")

# Test POs sorting
print("\n4. PURCHASE ORDERS (sorted by qb_txn_date DESC)")
print("-" * 80)
pos = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == 1).order_by(desc(PurchaseOrder.qb_txn_date)).limit(10).all()
for i, po in enumerate(pos, 1):
    print(f"{i:2}. ID={po.id:3}, Doc={po.qb_doc_number:8}, TxnDate={po.qb_txn_date}, Vendor={po.qb_vendor_name}")

print("\n" + "=" * 80)
print("✓ Database sorting test complete!")
print("=" * 80)

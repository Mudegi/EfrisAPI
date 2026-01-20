"""
Add sample data to test the dashboard
"""
from database.connection import SessionLocal
from database.models import Product, Invoice
from datetime import datetime

def add_sample_data():
    """Add sample products and invoices"""
    db = SessionLocal()
    try:
        company_id = 1  # Wandera EFRIS
        
        # Check if data already exists
        existing_products = db.query(Product).filter(Product.company_id == company_id).count()
        if existing_products > 0:
            print(f"✓ Sample data already exists ({existing_products} products)")
            return
        
        print("Adding sample products...")
        
        # Sample Products
        products = [
            Product(
                company_id=company_id,
                qb_item_id="24",
                qb_name="Magulop",
                qb_sku="MAG001",
                efris_product_code="Magul12",
                efris_status="approved",
                has_excise=False
            ),
            Product(
                company_id=company_id,
                qb_item_id="18",
                qb_name="Cement",
                qb_sku="CEM001",
                efris_product_code="LED050000",
                efris_status="approved",
                has_excise=True,
                excise_duty_code="LED050000"
            ),
            Product(
                company_id=company_id,
                qb_item_id="12",
                qb_name="Consulting Services",
                qb_sku="CONS001",
                efris_product_code="",
                efris_status="pending",
                has_excise=False
            ),
            Product(
                company_id=company_id,
                qb_item_id="15",
                qb_name="Software License",
                qb_sku="SOFT001",
                efris_product_code="SOFT001",
                efris_status="approved",
                has_excise=False
            ),
            Product(
                company_id=company_id,
                qb_item_id="20",
                qb_name="Training Materials",
                qb_sku="TRAIN001",
                efris_product_code="TRAIN001",
                efris_status="approved",
                has_excise=False
            ),
        ]
        
        for product in products:
            db.add(product)
        
        print(f"✓ Added {len(products)} sample products")
        
        # Sample Invoices
        print("Adding sample invoices...")
        
        invoices = [
            Invoice(
                company_id=company_id,
                qb_invoice_id="153",
                qb_customer_name="Cool Cars",
                qb_total_amt=53100.00,
                efris_fdn="325042882327",
                efris_verification_code="26146625601610223649",
                efris_qr_code="https://efristest.ura.go.ug/site_new/#/invoiceValidation?invoiceNo=325042882327",
                efris_status="approved"
            ),
            Invoice(
                company_id=company_id,
                qb_invoice_id="152",
                qb_customer_name="ABC Limited",
                qb_total_amt=120000.00,
                efris_fdn="325042112458",
                efris_verification_code="12345678901234567890",
                efris_qr_code="https://efristest.ura.go.ug/site_new/#/invoiceValidation?invoiceNo=325042112458",
                efris_status="approved"
            ),
            Invoice(
                company_id=company_id,
                qb_invoice_id="151",
                qb_customer_name="XYZ Company",
                qb_total_amt=85500.00,
                efris_fdn="",
                efris_verification_code="",
                efris_qr_code="",
                efris_status="pending"
            ),
            Invoice(
                company_id=company_id,
                qb_invoice_id="150",
                qb_customer_name="Tech Solutions Ltd",
                qb_total_amt=245000.00,
                efris_fdn="325041998765",
                efris_verification_code="98765432109876543210",
                efris_qr_code="https://efristest.ura.go.ug/site_new/#/invoiceValidation?invoiceNo=325041998765",
                efris_status="approved"
            ),
            Invoice(
                company_id=company_id,
                qb_invoice_id="149",
                qb_customer_name="Global Traders",
                qb_total_amt=180000.00,
                efris_fdn="325041887654",
                efris_verification_code="55555555555555555555",
                efris_qr_code="https://efristest.ura.go.ug/site_new/#/invoiceValidation?invoiceNo=325041887654",
                efris_status="approved"
            ),
        ]
        
        for invoice in invoices:
            db.add(invoice)
        
        print(f"✓ Added {len(invoices)} sample invoices")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ SAMPLE DATA ADDED SUCCESSFULLY!")
        print("="*60)
        print(f"\nTotal Products: {len(products)}")
        print(f"Total Invoices: {len(invoices)}")
        print(f"Approved Invoices: {sum(1 for i in invoices if i.efris_status == 'approved')}")
        print("\nRefresh the dashboard to see the data!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()

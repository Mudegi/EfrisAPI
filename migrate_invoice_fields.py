"""
Add outgoing invoice fields to EFRISInvoice table
Run this to update the database schema for invoice submission tracking
"""
import sys
sys.path.insert(0, '.')

from database.connection import engine
from sqlalchemy import text

def migrate():
    
    with engine.connect() as conn:
        print("Adding new columns to efris_invoices table...")
        
        # Add QuickBooks reference fields
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS qb_invoice_id VARCHAR(100)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_efris_invoices_qb_id ON efris_invoices(qb_invoice_id)"))
            print("✓ Added qb_invoice_id")
        except Exception as e:
            print(f"  qb_invoice_id: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS qb_invoice_number VARCHAR(100)"))
            print("✓ Added qb_invoice_number")
        except Exception as e:
            print(f"  qb_invoice_number: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS invoice_date DATE"))
            print("✓ Added invoice_date")
        except Exception as e:
            print(f"  invoice_date: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255)"))
            print("✓ Added customer_name")
        except Exception as e:
            print(f"  customer_name: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS customer_tin VARCHAR(50)"))
            print("✓ Added customer_tin")
        except Exception as e:
            print(f"  customer_tin: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS buyer_type VARCHAR(10)"))
            print("✓ Added buyer_type")
        except Exception as e:
            print(f"  buyer_type: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS total_amount FLOAT"))
            print("✓ Added total_amount")
        except Exception as e:
            print(f"  total_amount: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS total_tax FLOAT"))
            print("✓ Added total_tax")
        except Exception as e:
            print(f"  total_tax: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS total_excise FLOAT"))
            print("✓ Added total_excise")
        except Exception as e:
            print(f"  total_excise: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS total_discount FLOAT"))
            print("✓ Added total_discount")
        except Exception as e:
            print(f"  total_discount: {e}")
        
        # Add submission tracking fields
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS status VARCHAR(50)"))
            print("✓ Added status")
        except Exception as e:
            print(f"  status: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS fdn VARCHAR(100)"))
            print("✓ Added fdn")
        except Exception as e:
            print(f"  fdn: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS efris_invoice_id VARCHAR(100)"))
            print("✓ Added efris_invoice_id")
        except Exception as e:
            print(f"  efris_invoice_id: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS submission_date TIMESTAMP"))
            print("✓ Added submission_date")
        except Exception as e:
            print(f"  submission_date: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS error_message TEXT"))
            print("✓ Added error_message")
        except Exception as e:
            print(f"  error_message: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS efris_payload JSONB"))
            print("✓ Added efris_payload")
        except Exception as e:
            print(f"  efris_payload: {e}")
        
        try:
            conn.execute(text("ALTER TABLE efris_invoices ADD COLUMN IF NOT EXISTS efris_response JSONB"))
            print("✓ Added efris_response")
        except Exception as e:
            print(f"  efris_response: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == '__main__':
    migrate()

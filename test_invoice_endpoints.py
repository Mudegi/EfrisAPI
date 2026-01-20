"""
Quick test for invoice posting endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"
COMPANY_ID = 1  # Replace with your company ID

def test_get_invoices():
    """Test getting QuickBooks invoices"""
    print("\n=== Testing GET QuickBooks Invoices ===")
    url = f"{BASE_URL}/api/companies/{COMPANY_ID}/quickbooks/invoices"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"Found {len(invoices)} invoices")
            
            if invoices:
                # Show first invoice
                invoice = invoices[0]
                print(f"\nFirst Invoice:")
                print(f"  ID: {invoice.get('Id')}")
                print(f"  DocNumber: {invoice.get('DocNumber')}")
                print(f"  Customer: {invoice.get('CustomerRef', {}).get('name')}")
                print(f"  TotalAmt: {invoice.get('TotalAmt')}")
                print(f"  EFRIS Status: {invoice.get('EfrisStatus', 'draft')}")
                print(f"  EFRIS FDN: {invoice.get('EfrisFDN', 'N/A')}")
                
                return invoice.get('Id')
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_get_invoice_details(invoice_id):
    """Test getting invoice details with enriched metadata"""
    print(f"\n=== Testing GET Invoice Details (ID: {invoice_id}) ===")
    url = f"{BASE_URL}/api/companies/{COMPANY_ID}/qb-invoice/{invoice_id}"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            invoice = response.json()
            print(f"\nInvoice Details:")
            print(f"  DocNumber: {invoice.get('DocNumber')}")
            print(f"  Customer: {invoice.get('CustomerRef', {}).get('name')}")
            print(f"  Date: {invoice.get('TxnDate')}")
            print(f"  TotalAmt: {invoice.get('TotalAmt')}")
            
            lines = invoice.get('Line', [])
            item_lines = [l for l in lines if l.get('DetailType') == 'SalesItemLineDetail']
            print(f"\n  {len(item_lines)} line items:")
            
            for i, line in enumerate(item_lines, 1):
                detail = line.get('SalesItemLineDetail', {})
                item_details = detail.get('ItemDetails', {})
                
                print(f"\n  Line {i}:")
                print(f"    Item: {item_details.get('Name', 'N/A')}")
                print(f"    Qty: {detail.get('Qty', 0)}")
                print(f"    UnitPrice: {detail.get('UnitPrice', 0)}")
                print(f"    Amount: {line.get('Amount', 0)}")
                print(f"    Tax Rate: {item_details.get('TaxRate', 0) * 100}%")
                
                if item_details.get('HasExcise'):
                    print(f"    Excise Code: {item_details.get('ExciseDutyCode')}")
                    print(f"    Excise Rule: {item_details.get('ExciseRule')}")
                    print(f"    Excise Rate: {item_details.get('ExciseRate')}")
            
            return invoice
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_submit_invoice(invoice_id):
    """Test submitting invoice to EFRIS"""
    print(f"\n=== Testing Submit Invoice to EFRIS (ID: {invoice_id}) ===")
    url = f"{BASE_URL}/api/companies/{COMPANY_ID}/invoices/submit-to-efris"
    
    # Sample payload - adjust based on actual invoice
    payload = {
        "invoice_id": invoice_id,
        "invoice_data": {
            "TxnDate": "2024-01-15",
            "BuyerType": "1",  # 0=Business, 1=Individual
            "BuyerTIN": ""  # Optional for individuals
        }
    }
    
    try:
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Uncomment to actually submit
        # response = requests.post(url, json=payload)
        # print(f"Status: {response.status_code}")
        # print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n⚠️  Test submission disabled - uncomment code to submit")
        
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("INVOICE POSTING ENDPOINTS TEST")
    print("=" * 60)
    
    # Test 1: Get invoices list
    invoice_id = test_get_invoices()
    
    # Test 2: Get invoice details
    if invoice_id:
        invoice = test_get_invoice_details(invoice_id)
        
        # Test 3: Submit to EFRIS (disabled by default)
        if invoice:
            test_submit_invoice(invoice_id)
    else:
        print("\n⚠️  No invoices found. Import from QuickBooks first.")
    
    print("\n" + "=" * 60)
    print("✓ Tests completed")
    print("=" * 60)

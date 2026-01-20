"""
Diagnostic script to troubleshoot Purchase Order to EFRIS sync issues
This checks what product codes are being used vs what's registered in EFRIS
"""
import requests
import json

BASE_URL = "http://localhost:8001"

# Replace with your actual credentials
EMAIL = "admin@wandera.com"
PASSWORD = "Admin2026!"

def login():
    """Login and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": EMAIL,
        "password": PASSWORD
    })
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Login failed: {response.status_code}")
        return None

def diagnose_po_sync(token, company_id=1):
    """Diagnose PO sync issues"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 80)
    print("PURCHASE ORDER TO EFRIS DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # 1. Get Purchase Orders
    print("📋 Step 1: Checking Purchase Orders...")
    po_response = requests.get(
        f"{BASE_URL}/api/companies/{company_id}/qb-purchase-orders",
        headers=headers
    )
    
    if po_response.status_code != 200:
        print(f"❌ Failed to get purchase orders: {po_response.status_code}")
        return
    
    pos = po_response.json()
    print(f"✓ Found {len(pos)} purchase orders")
    print()
    
    # 2. Get EFRIS Registered Goods
    print("📦 Step 2: Checking EFRIS Registered Products...")
    goods_response = requests.get(
        f"{BASE_URL}/api/companies/{company_id}/efris-goods",
        headers=headers
    )
    
    if goods_response.status_code != 200:
        print(f"❌ Failed to get EFRIS goods: {goods_response.status_code}")
        return
    
    efris_goods = goods_response.json()
    registered_codes = {g['goods_code'].strip() for g in efris_goods if g.get('goods_code')}
    print(f"✓ Found {len(registered_codes)} products registered in EFRIS")
    print()
    
    # 3. Analyze each PO
    print("🔍 Step 3: Analyzing Purchase Orders...")
    print("=" * 80)
    
    for po in pos:
        doc_number = po.get('doc_number', 'N/A')
        status = po.get('efris_status', 'pending')
        
        print(f"\n📄 PO #{doc_number}")
        print(f"   Status: {status}")
        print(f"   Vendor: {po.get('vendor_name', 'N/A')}")
        print(f"   Date: {po.get('txn_date', 'N/A')}")
        print(f"   Amount: UGX {po.get('total_amt', 0):,.0f}")
        
        if po.get('efris_error'):
            print(f"   ❌ Error: {po['efris_error']}")
        
        # Check line items
        qb_data = po.get('qb_data', {})
        lines = qb_data.get('Line', [])
        
        print(f"\n   Line Items:")
        for line in lines:
            if line.get('DetailType') == 'ItemBasedExpenseLineDetail':
                detail = line.get('ItemBasedExpenseLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                item_name = item_ref.get('name', 'Unknown')
                item_id = item_ref.get('value', '')
                qty = detail.get('Qty', 0)
                
                # Try to determine what product code will be used
                # Check products table
                product_response = requests.get(
                    f"{BASE_URL}/api/companies/{company_id}/qb-items",
                    headers=headers
                )
                
                product_code = item_name  # Default fallback
                if product_response.status_code == 200:
                    products_data = product_response.json()
                    products = products_data.get('items', [])
                    matching_product = next((p for p in products if p['Id'] == item_id), None)
                    if matching_product and matching_product.get('Description'):
                        product_code = matching_product['Description']
                
                is_registered = product_code.strip() in registered_codes
                status_icon = "✓" if is_registered else "❌"
                
                print(f"      {status_icon} {item_name}")
                print(f"         Code that will be sent: '{product_code}'")
                print(f"         Registered in EFRIS: {is_registered}")
                print(f"         Quantity: {qty}")
                
                if not is_registered:
                    print(f"         ⚠️  WARNING: This product code is NOT registered in EFRIS!")
                    print(f"         ⚠️  Stock increase will be ignored by EFRIS")
                    
                    # Find similar codes
                    similar = [code for code in registered_codes if item_name.lower() in code.lower() or code.lower() in item_name.lower()]
                    if similar:
                        print(f"         💡 Similar codes in EFRIS: {', '.join(similar[:3])}")
        
        print()
    
    print("=" * 80)
    print("\n📊 SUMMARY")
    print("=" * 80)
    print(f"Total POs: {len(pos)}")
    print(f"Pending: {sum(1 for p in pos if p.get('efris_status') in [None, 'pending'])}")
    print(f"Sent: {sum(1 for p in pos if p.get('efris_status') == 'sent')}")
    print(f"Failed: {sum(1 for p in pos if p.get('efris_status') == 'failed')}")
    print()
    print("📝 EFRIS Registered Product Codes:")
    for code in sorted(list(registered_codes)[:20]):  # Show first 20
        print(f"   - {code}")
    if len(registered_codes) > 20:
        print(f"   ... and {len(registered_codes) - 20} more")
    
    print()
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    print("1. Ensure all products in QuickBooks have their Description field set to the EFRIS product code")
    print("2. Or, import items to database and set the correct EFRIS product codes there")
    print("3. Register any missing products in EFRIS first (T130) before sending POs")
    print("4. Product codes must match EXACTLY (case-sensitive)")
    print()

if __name__ == "__main__":
    token = login()
    if token:
        diagnose_po_sync(token)

"""
Test script demonstrating discount and tax handling for EFRIS
This shows how a QuickBooks invoice with 10% discount and 18% tax is mapped to EFRIS format
"""
import json
from quickbooks_efris_mapper import QuickBooksEfrisMapper

# Sample QuickBooks invoice with 10% discount and 18% tax
qb_invoice = {
    "DocNumber": "INV-001",
    "TxnDate": "2026-01-18",
    "Line": [
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 10620.00,  # Final amount with tax (after 10% discount)
            "SalesItemLineDetail": {
                "ItemRef": {
                    "value": "1",
                    "name": "Coffee Beans"
                },
                "Qty": 10,
                "UnitPrice": 1000.00,  # Original price per unit
                "DiscountRate": 10,  # 10% discount
                "ItemDetails": {
                    "Name": "Coffee Beans",
                    "Description": "COFFEE001",
                    "Sku": "50202306",
                    "UnitOfMeasure": "102",  # Kilogram
                    "HasExcise": False
                }
            }
        },
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 23600.00,  # No discount on this item
            "SalesItemLineDetail": {
                "ItemRef": {
                    "value": "2",
                    "name": "Tea Leaves"
                },
                "Qty": 20,
                "UnitPrice": 1000.00,
                "ItemDetails": {
                    "Name": "Tea Leaves",
                    "Description": "TEA001",
                    "Sku": "50202307",
                    "UnitOfMeasure": "102",
                    "HasExcise": False
                }
            }
        }
    ],
    "BuyerType": "1"
}

# Sample customer info
qb_customer = {
    "DisplayName": "Test Customer",
    "PrimaryEmailAddr": {
        "Address": "customer@example.com"
    },
    "PrimaryPhone": {
        "FreeFormNumber": "0700123456"
    },
    "BillAddr": {
        "Line1": "123 Main St",
        "City": "Kampala",
        "Country": "Uganda"
    }
}

# Sample company info
company_info = {
    "CompanyName": "My Company Ltd",
    "EfrisTin": "1014409555",
    "EfrisDeviceNo": "1014409555_01",
    "PrimaryPhone": {
        "FreeFormNumber": "0700999888"
    },
    "Email": {
        "Address": "company@example.com"
    },
    "CompanyAddr": {
        "Line1": "Plot 100 Industrial Area",
        "City": "Kampala",
        "Country": "Uganda"
    }
}

def main():
    print("=" * 80)
    print("DISCOUNT AND TAX HANDLING TEST")
    print("=" * 80)
    print()
    
    # Map the invoice
    print("📋 Mapping QuickBooks invoice to EFRIS format...")
    print()
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print()
    print("=" * 80)
    print("EFRIS INVOICE - goodsDetails")
    print("=" * 80)
    print()
    
    for i, item in enumerate(efris_invoice['goodsDetails'], 1):
        print(f"Item {i}: {item['item']}")
        print(f"  Quantity: {item['qty']}")
        print(f"  Unit Price: {item['unitPrice']} UGX")
        print(f"  Total Amount: {item['total']} UGX")
        print()
        
        # Check if item has discount
        if item['discountFlag'] == "1":
            print(f"  ✅ HAS DISCOUNT:")
            print(f"     - Discount Amount: {item['discountTotal']} UGX")
            print(f"     - Discount Tax Rate: {item['discountTaxRate']}")
            
            # Calculate discount percentage
            original = float(item['qty']) * float(item['unitPrice'])
            discount = float(item['discountTotal'])
            discount_pct = (discount / original) * 100
            print(f"     - Discount Percentage: {discount_pct:.1f}%")
        else:
            print(f"  ⭕ NO DISCOUNT")
        
        print()
        print(f"  📊 TAX INFORMATION:")
        print(f"     - Tax Rate: {item['taxRate']} (18% VAT)")
        print(f"     - VAT Amount: {item['tax']} UGX")
        
        # Calculate breakdown
        total_with_vat = float(item['total'])
        vat = float(item['tax'])
        net = total_with_vat - vat
        
        print(f"     - Net Amount (before VAT): {net:.2f} UGX")
        print(f"     - Gross Amount (with VAT): {total_with_vat:.2f} UGX")
        print()
        print("-" * 80)
        print()
    
    # Summary
    summary = efris_invoice['summary']
    print("=" * 80)
    print("INVOICE SUMMARY")
    print("=" * 80)
    print(f"Total Items: {summary['itemCount']}")
    print(f"Net Amount: {summary['netAmount']} UGX")
    print(f"Total VAT: {summary['taxAmount']} UGX")
    print(f"Gross Amount: {summary['grossAmount']} UGX")
    print()
    
    # Save to file for inspection
    output_file = "test_discount_output.json"
    with open(output_file, 'w') as f:
        json.dump(efris_invoice, f, indent=2)
    
    print(f"✅ Full EFRIS invoice saved to: {output_file}")
    print()
    
    # Validation checks
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    
    all_valid = True
    
    for i, item in enumerate(efris_invoice['goodsDetails'], 1):
        print(f"Item {i}: ", end="")
        
        # Check discount consistency
        if item['discountFlag'] == "1":
            if not item['discountTotal'] or item['discountTotal'] == "":
                print("❌ FAIL: discountFlag is 1 but discountTotal is empty")
                all_valid = False
            elif not item['discountTaxRate'] or item['discountTaxRate'] == "":
                print("❌ FAIL: discountFlag is 1 but discountTaxRate is empty")
                all_valid = False
            else:
                print("✅ PASS: Discount fields valid")
        else:
            if item['discountTotal'] != "":
                print("❌ FAIL: discountFlag is 2 but discountTotal is not empty")
                all_valid = False
            elif item['discountTaxRate'] != "":
                print("❌ FAIL: discountFlag is 2 but discountTaxRate is not empty")
                all_valid = False
            else:
                print("✅ PASS: No discount fields valid")
    
    print()
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED - Ready to send to EFRIS!")
    else:
        print("⚠️  VALIDATION FAILED - Please review the errors above")
    print()

if __name__ == "__main__":
    main()

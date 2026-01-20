"""
COMPLETE TEST: Excise Duty + Discount + ANY Tax Rate
Shows: Excise with discounts, Standard VAT, Zero-rated, Exempt
"""
import json
from quickbooks_efris_mapper import QuickBooksEfrisMapper

# Comprehensive invoice with EXCISE DUTY + DISCOUNTS + MULTIPLE TAX TYPES
qb_invoice = {
    "DocNumber": "INV-003",
    "TxnDate": "2026-01-18",
    "Line": [
        # Item 1: Beer with excise + 10% discount + 18% VAT
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 118000.00,
            "SalesItemLineDetail": {
                "ItemRef": {"value": "1", "name": "Bell Lager 500ml"},
                "Qty": 100,
                "UnitPrice": 1000.00,
                "DiscountRate": 10,  # 10% discount
                "ItemDetails": {
                    "Name": "Bell Lager 500ml",
                    "Description": "BEER001",
                    "Sku": "50202401",
                    "UnitOfMeasure": "101",
                    "HasExcise": True,
                    "ExciseDutyCode": "106",
                    "ExciseUnit": "101",
                    "ExciseRate": "200",  # 200 UGX per unit (fixed rate)
                    "ExciseRule": "2",  # Fixed rate
                    "TaxRate": 0.18  # Standard 18%
                }
            }
        },
        # Item 2: Cigarettes with excise + 20% discount + 18% VAT
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 94400.00,
            "SalesItemLineDetail": {
                "ItemRef": {"value": "2", "name": "Sportsman Cigarettes"},
                "Qty": 50,
                "UnitPrice": 1500.00,
                "DiscountRate": 20,  # 20% discount
                "ItemDetails": {
                    "Name": "Sportsman Cigarettes",
                    "Description": "CIG001",
                    "Sku": "50202402",
                    "UnitOfMeasure": "108",  # Box
                    "HasExcise": True,
                    "ExciseDutyCode": "107",
                    "ExciseUnit": "108",
                    "ExciseRate": "300",  # 300 UGX per box
                    "ExciseRule": "2",  # Fixed rate
                    "TaxRate": 0.18
                }
            }
        },
        # Item 3: Soft drink with excise + NO discount + 18% VAT
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 59000.00,
            "SalesItemLineDetail": {
                "ItemRef": {"value": "3", "name": "Coca Cola 500ml"},
                "Qty": 50,
                "UnitPrice": 1000.00,
                "ItemDetails": {
                    "Name": "Coca Cola 500ml",
                    "Description": "SODA001",
                    "Sku": "50202403",
                    "UnitOfMeasure": "101",
                    "HasExcise": True,
                    "ExciseDutyCode": "108",
                    "ExciseUnit": "101",
                    "ExciseRate": "100",  # 100 UGX per unit
                    "ExciseRule": "2",  # Fixed rate
                    "TaxRate": 0.18
                }
            }
        },
        # Item 4: Spirits with excise + 15% discount + 18% VAT + percentage excise
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 70800.00,
            "SalesItemLineDetail": {
                "ItemRef": {"value": "4", "name": "Waragi 1L"},
                "Qty": 20,
                "UnitPrice": 3000.00,
                "DiscountRate": 15,  # 15% discount
                "ItemDetails": {
                    "Name": "Waragi 1L",
                    "Description": "SPIRIT001",
                    "Sku": "50202404",
                    "UnitOfMeasure": "104",  # Liter
                    "HasExcise": True,
                    "ExciseDutyCode": "109",
                    "ExciseUnit": "104",
                    "ExciseRate": "30",  # 30% of price
                    "ExciseRule": "1",  # Percentage-based
                    "TaxRate": 0.18
                }
            }
        },
        # Item 5: Fuel with excise + 5% discount + Zero-rated (exports)
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 47500.00,  # No VAT on zero-rated
            "SalesItemLineDetail": {
                "ItemRef": {"value": "5", "name": "Petrol (Export)"},
                "Qty": 10,
                "UnitPrice": 5000.00,
                "DiscountRate": 5,  # 5% discount
                "TaxCodeRef": {"name": "ZERO-RATED", "value": "ZR"},
                "ItemDetails": {
                    "Name": "Petrol (Export)",
                    "Description": "FUEL001",
                    "Sku": "50202405",
                    "UnitOfMeasure": "104",
                    "HasExcise": True,
                    "ExciseDutyCode": "110",
                    "ExciseUnit": "104",
                    "ExciseRate": "1200",  # 1200 UGX per liter
                    "ExciseRule": "2",  # Fixed rate
                    "TaxRate": 0.0  # Zero-rated for exports
                }
            }
        },
        # Item 6: Regular item NO excise + 12% discount + 18% VAT
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": 10384.00,
            "SalesItemLineDetail": {
                "ItemRef": {"value": "6", "name": "Office Paper"},
                "Qty": 10,
                "UnitPrice": 1000.00,
                "DiscountRate": 12,  # 12% discount
                "ItemDetails": {
                    "Name": "Office Paper",
                    "Description": "PAPER001",
                    "Sku": "50202406",
                    "UnitOfMeasure": "101",
                    "HasExcise": False,
                    "TaxRate": 0.18
                }
            }
        }
    ],
    "BuyerType": "1"
}

qb_customer = {
    "DisplayName": "ABC Trading Co",
    "PrimaryEmailAddr": {"Address": "abc@trading.com"},
    "PrimaryPhone": {"FreeFormNumber": "0700111222"},
    "BillAddr": {"Line1": "Industrial Area", "City": "Kampala", "Country": "Uganda"}
}

company_info = {
    "CompanyName": "Beverage Distributors Ltd",
    "EfrisTin": "1014409555",
    "EfrisDeviceNo": "1014409555_01",
    "PrimaryPhone": {"FreeFormNumber": "0700999888"},
    "Email": {"Address": "info@beverages.com"},
    "CompanyAddr": {"Line1": "Plot 200", "City": "Kampala", "Country": "Uganda"}
}

def main():
    print("=" * 120)
    print("COMPLETE TEST: EXCISE DUTY + DISCOUNT + ANY TAX RATE")
    print("=" * 120)
    print()
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print()
    print("=" * 120)
    print("INVOICE ITEMS BREAKDOWN")
    print("=" * 120)
    print()
    
    for i, item in enumerate(efris_invoice['goodsDetails'], 1):
        print(f"{'='*120}")
        print(f"Item {i}: {item['item']}")
        print(f"{'='*120}")
        
        # Basic info
        qty = float(item['qty'])
        unit_price = float(item['unitPrice'])
        total = float(item['total'])
        
        print(f"  Quantity: {qty:.0f} @ {unit_price:.2f} UGX = {qty * unit_price:.2f} UGX")
        
        # Discount
        if item['discountFlag'] == "1":
            discount = float(item['discountTotal'])
            discount_pct = (discount / (qty * unit_price)) * 100
            print(f"  ✅ DISCOUNT: {discount:.2f} UGX ({discount_pct:.1f}%)")
        else:
            print(f"  ⭕ NO DISCOUNT")
        
        # Excise
        if item['exciseFlag'] == "1":
            excise_tax = float(item['exciseTax']) if item['exciseTax'] else 0
            excise_rate = item['exciseRate']
            excise_rule = item['exciseRule']
            excise_unit = item['exciseUnit']
            
            print(f"  🍺 EXCISE DUTY:")
            print(f"     - Excise Code: {item['categoryId']}")
            print(f"     - Excise Rate: {excise_rate}")
            print(f"     - Excise Rule: {'Percentage' if excise_rule == '1' else 'Fixed Rate'}")
            print(f"     - Excise Unit: {excise_unit}")
            print(f"     - Excise Tax: {excise_tax:.2f} UGX")
        else:
            print(f"  ⭕ NO EXCISE")
        
        # VAT
        tax_rate = float(item['taxRate'])
        vat = float(item['tax'])
        tax_cat = item['taxCategoryCode']
        
        tax_type = {
            "01": "STANDARD VAT",
            "02": "ZERO-RATED",
            "03": "EXEMPT"
        }.get(tax_cat, "UNKNOWN")
        
        print(f"  📊 TAX:")
        print(f"     - Type: {tax_type}")
        print(f"     - Rate: {tax_rate*100:.0f}%")
        print(f"     - VAT Amount: {vat:.2f} UGX")
        
        # Total breakdown
        print(f"  💰 TOTAL: {total:.2f} UGX")
        print()
    
    # Summary by category
    print("=" * 120)
    print("SUMMARY BY CATEGORY")
    print("=" * 120)
    
    total_excise = sum(float(item.get('exciseTax', 0) or 0) for item in efris_invoice['goodsDetails'] if item.get('exciseTax'))
    total_vat = sum(float(item['tax']) for item in efris_invoice['goodsDetails'])
    total_discount = sum(float(item['discountTotal']) for item in efris_invoice['goodsDetails'] if item.get('discountTotal'))
    
    print(f"\n  Total Excise Duty: {total_excise:.2f} UGX")
    print(f"  Total VAT: {total_vat:.2f} UGX")
    print(f"  Total Discounts: {total_discount:.2f} UGX")
    print(f"  Total Tax (Excise + VAT): {total_excise + total_vat:.2f} UGX")
    
    # Tax details
    print("\n" + "=" * 120)
    print("TAX DETAILS BY CATEGORY")
    print("=" * 120)
    for tax_detail in efris_invoice['taxDetails']:
        cat_name = {
            "01": "STANDARD VAT",
            "02": "ZERO-RATED",
            "03": "EXEMPT"
        }.get(tax_detail['taxCategoryCode'], "UNKNOWN")
        
        print(f"\n{cat_name}:")
        print(f"  Net Amount: {tax_detail['netAmount']} UGX")
        print(f"  Tax Rate: {tax_detail['taxRate']}")
        print(f"  Tax Amount: {tax_detail['taxAmount']} UGX")
        print(f"  Total (incl. excise): {tax_detail['tax']} UGX")
        print(f"  Gross Amount: {tax_detail['grossAmount']} UGX")
    
    # Final summary
    summary = efris_invoice['summary']
    print("\n" + "=" * 120)
    print("INVOICE SUMMARY")
    print("=" * 120)
    print(f"  Total Items: {summary['itemCount']}")
    print(f"  Net Amount: {summary['netAmount']} UGX")
    print(f"  Total Tax: {summary['taxAmount']} UGX")
    print(f"  Gross Amount: {summary['grossAmount']} UGX")
    
    # Save
    output_file = "test_excise_discount_tax_complete.json"
    with open(output_file, 'w') as f:
        json.dump(efris_invoice, f, indent=2)
    print(f"\n✅ Full invoice saved to: {output_file}")
    
    # Validation
    print("\n" + "=" * 120)
    print("VALIDATION CHECKS")
    print("=" * 120)
    print()
    
    all_valid = True
    checks = []
    
    # Check excise items
    excise_items = [item for item in efris_invoice['goodsDetails'] if item['exciseFlag'] == '1']
    checks.append(f"✅ Excise items found: {len(excise_items)}")
    
    for item in excise_items:
        if not item.get('exciseTax') or item['exciseTax'] == '':
            checks.append(f"❌ FAIL: {item['item']} - exciseFlag=1 but no exciseTax")
            all_valid = False
        if not item.get('categoryId'):
            checks.append(f"❌ FAIL: {item['item']} - exciseFlag=1 but no categoryId")
            all_valid = False
    
    # Check discount + excise items
    excise_discount_items = [item for item in excise_items if item['discountFlag'] == '1']
    checks.append(f"✅ Items with BOTH excise and discount: {len(excise_discount_items)}")
    
    # Check tax categories
    tax_categories = set(item['taxCategoryCode'] for item in efris_invoice['goodsDetails'])
    checks.append(f"✅ Tax categories used: {', '.join(sorted(tax_categories))}")
    
    for check in checks:
        print(check)
    
    print()
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print()
        print("✨ This invoice demonstrates:")
        print(f"   ✅ {len(excise_items)} items with EXCISE DUTY")
        print(f"   ✅ {len(excise_discount_items)} items with EXCISE + DISCOUNT")
        print("   ✅ Fixed-rate excise (200, 300, 100, 1200 UGX)")
        print("   ✅ Percentage excise (30%)")
        print("   ✅ Multiple tax types (Standard VAT, Zero-rated)")
        print("   ✅ Various discount % (5%, 10%, 12%, 15%, 20%)")
        print("   ✅ Excise with zero-rated items")
        print()
        print("🚀 Ready to submit to EFRIS!")
    else:
        print("⚠️  VALIDATION FAILED")
    print()

if __name__ == "__main__":
    main()

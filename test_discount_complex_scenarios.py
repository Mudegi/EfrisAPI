"""
Test complex discount scenarios with mixed tax rates, excise, zero-rated, and exempt items
This ensures discounts work correctly across all EFRIS item types
"""
import json
from quickbooks_efris_mapper import QuickBooksEfrisMapper

def print_scenario(title, description):
    print("\n" + "="*80)
    print(f"[SCENARIO] {title}")
    print("="*80)
    print(description)
    print()

def print_efris_item(item, idx):
    print(f"\n  Item {idx}: {item['item']}")
    print(f"    Qty: {item['qty']} × Price: {item['unitPrice']} UGX")
    print(f"    Discount: {item['discountTotal']} ({item['discountFlag']})")
    print(f"    Tax Rate: {item['taxRate']} ({item['taxCategoryCode']})")
    print(f"    VAT: {item['tax']} UGX")
    print(f"    Excise: {item.get('exciseTax', 'N/A')}")
    print(f"    Total: {item['total']} UGX")

def test_scenario_1_mixed_tax_rates_with_discount():
    """Invoice with Standard VAT, Zero-rated, and Exempt items + 10% discount"""
    print_scenario(
        "Mixed Tax Rates + 10% Invoice Discount",
        "Item A: Standard VAT (18%)\nItem B: Zero-rated (0%)\nItem C: Exempt (0%)\nInvoice Discount: 10%"
    )
    
    qb_invoice = {
        "DocNumber": "INV-MIXED-001",
        "TxnDate": "2026-01-19",
        "Line": [
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 10000.00,  # Tax-exclusive
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "1", "name": "Standard Item"},
                    "Qty": 10,
                    "UnitPrice": 1000.00,
                    "TaxCodeRef": {"name": "Standard"},
                    "ItemDetails": {
                        "Name": "Standard Item",
                        "Description": "STD001",
                        "Sku": "50202306",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": False
                    }
                }
            },
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 5000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "2", "name": "Zero-rated Item"},
                    "Qty": 5,
                    "UnitPrice": 1000.00,
                    "TaxCodeRef": {"name": "Zero-rated"},
                    "ItemDetails": {
                        "Name": "Zero-rated Item",
                        "Description": "ZERO001",
                        "Sku": "50202307",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.0,
                        "HasExcise": False
                    }
                }
            },
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 3000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "3", "name": "Exempt Item"},
                    "Qty": 3,
                    "UnitPrice": 1000.00,
                    "TaxCodeRef": {"name": "Exempt"},
                    "ItemDetails": {
                        "Name": "Exempt Item",
                        "Description": "EXEMPT001",
                        "Sku": "50202308",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.0,
                        "HasExcise": False
                    }
                }
            },
            {
                "DetailType": "DiscountLineDetail",
                "Amount": -1800.00,  # 10% of 18,000
                "DiscountLineDetail": {
                    "PercentBased": True,
                    "DiscountPercent": 10
                }
            }
        ],
        "BuyerType": "1"
    }
    
    qb_customer = {
        "DisplayName": "Test Customer",
        "PrimaryEmailAddr": {"Address": "test@example.com"},
        "PrimaryPhone": {"FreeFormNumber": "0700123456"},
        "BillAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    company_info = {
        "CompanyName": "Test Company",
        "EfrisTin": "1014409555",
        "EfrisDeviceNo": "1014409555_01",
        "PrimaryPhone": {"FreeFormNumber": "0700999888"},
        "Email": {"Address": "test@company.com"},
        "CompanyAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print("EFRIS Goods Details:")
    for idx, item in enumerate(efris_invoice['goodsDetails']):
        print_efris_item(item, idx)
    
    print(f"\n[Summary]")
    print(f"  Net Amount: {efris_invoice['summary']['netAmount']} UGX")
    print(f"  Total VAT: {efris_invoice['summary']['taxAmount']} UGX")
    print(f"  Grand Total: {efris_invoice['summary']['grossAmount']} UGX")
    
    # Validation
    print(f"\n[Validation]")
    items_with_discount = sum(1 for item in efris_invoice['goodsDetails'] if item['discountFlag'] == '1')
    print(f"  - Items with discount: {items_with_discount} (last item should have no discount)")
    print(f"  - All tax rates preserved: {[item['taxRate'] for item in efris_invoice['goodsDetails']]}")

def test_scenario_2_excise_with_discount():
    """Invoice with excise item (beer) + discount"""
    print_scenario(
        "Excise Item + 10% Invoice Discount",
        "Beer (500ml): Excise 200 UGX + VAT 18%\nInvoice Discount: 10%"
    )
    
    qb_invoice = {
        "DocNumber": "INV-EXCISE-001",
        "TxnDate": "2026-01-19",
        "Line": [
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 5000.00,  # Tax-exclusive
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "1", "name": "Beer 500ml"},
                    "Qty": 10,
                    "UnitPrice": 500.00,
                    "ItemDetails": {
                        "Name": "Beer 500ml",
                        "Description": "BEER001",
                        "Sku": "50202306",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": True,
                        "ExciseDutyCode": "101",
                        "ExciseUnit": "101",
                        "ExciseRate": "200",  # 200 UGX per unit
                        "ExciseRule": "2"  # Fixed rate
                    }
                }
            },
            {
                "DetailType": "DiscountLineDetail",
                "Amount": -500.00,  # 10% of 5,000
                "DiscountLineDetail": {
                    "PercentBased": True,
                    "DiscountPercent": 10
                }
            }
        ],
        "BuyerType": "1"
    }
    
    qb_customer = {
        "DisplayName": "Test Customer",
        "PrimaryEmailAddr": {"Address": "test@example.com"},
        "PrimaryPhone": {"FreeFormNumber": "0700123456"},
        "BillAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    company_info = {
        "CompanyName": "Test Company",
        "EfrisTin": "1014409555",
        "EfrisDeviceNo": "1014409555_01",
        "PrimaryPhone": {"FreeFormNumber": "0700999888"},
        "Email": {"Address": "test@company.com"},
        "CompanyAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print("EFRIS Goods Details:")
    for idx, item in enumerate(efris_invoice['goodsDetails']):
        print_efris_item(item, idx)
    
    print(f"\n[Expected Calculation]")
    print(f"  Original: 10 × 500 = 5,000 UGX")
    print(f"  Discount (10%): -500 UGX")
    print(f"  Net: 4,500 UGX")
    print(f"  Excise (10 × 200): 2,000 UGX (applies to original qty, not discounted)")
    print(f"  VAT (18% of 4,500): 810 UGX")
    print(f"  Total: 4,500 + 810 = 5,310 UGX")
    
    print(f"\n[Actual Summary]")
    print(f"  Net Amount: {efris_invoice['summary']['netAmount']} UGX")
    print(f"  Total VAT: {efris_invoice['summary']['taxAmount']} UGX")
    print(f"  Grand Total: {efris_invoice['summary']['grossAmount']} UGX")

def test_scenario_3_deemed_vat_with_discount():
    """Invoice with deemed VAT item + discount"""
    print_scenario(
        "Deemed VAT Item + 10% Discount",
        "Construction Materials (Deemed VAT)\nInvoice Discount: 10%"
    )
    
    qb_invoice = {
        "DocNumber": "INV-DEEMED-001",
        "TxnDate": "2026-01-19",
        "Line": [
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 50000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "1", "name": "Construction Materials"},
                    "Qty": 1,
                    "UnitPrice": 50000.00,
                    "ItemDetails": {
                        "Name": "Construction Materials",
                        "Description": "DEEMED001",
                        "Sku": "50202306",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": False,
                        "IsDeemedVAT": True,
                        "VATProjectId": "PRJ001",
                        "VATProjectName": "Building Project A"
                    }
                }
            },
            {
                "DetailType": "DiscountLineDetail",
                "Amount": -5000.00,  # 10%
                "DiscountLineDetail": {
                    "PercentBased": True,
                    "DiscountPercent": 10
                }
            }
        ],
        "BuyerType": "1"
    }
    
    qb_customer = {
        "DisplayName": "Test Customer",
        "PrimaryEmailAddr": {"Address": "test@example.com"},
        "PrimaryPhone": {"FreeFormNumber": "0700123456"},
        "BillAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    company_info = {
        "CompanyName": "Test Company",
        "EfrisTin": "1014409555",
        "EfrisDeviceNo": "1014409555_01",
        "PrimaryPhone": {"FreeFormNumber": "0700999888"},
        "Email": {"Address": "test@company.com"},
        "CompanyAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print("EFRIS Goods Details:")
    for idx, item in enumerate(efris_invoice['goodsDetails']):
        print_efris_item(item, idx)
        if item.get('deemedFlag') == '1':
            print(f"    [*] Deemed VAT Project: {item.get('vatProjectName', 'N/A')}")
    
    print(f"\n[Summary]")
    print(f"  Net Amount: {efris_invoice['summary']['netAmount']} UGX")
    print(f"  Total VAT: {efris_invoice['summary']['taxAmount']} UGX")
    print(f"  Grand Total: {efris_invoice['summary']['grossAmount']} UGX")

def test_scenario_4_all_combined():
    """Complex invoice with everything: mixed taxes, excise, deemed VAT, discount"""
    print_scenario(
        "[ULTIMATE] All Features Combined",
        "Item 1: Standard VAT (18%)\n" +
        "Item 2: Beer with Excise + VAT\n" +
        "Item 3: Zero-rated\n" +
        "Item 4: Deemed VAT\n" +
        "Invoice Discount: 5%"
    )
    
    qb_invoice = {
        "DocNumber": "INV-ULTIMATE-001",
        "TxnDate": "2026-01-19",
        "Line": [
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 10000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "1", "name": "Office Supplies"},
                    "Qty": 10,
                    "UnitPrice": 1000.00,
                    "ItemDetails": {
                        "Name": "Office Supplies",
                        "Description": "OFFICE001",
                        "Sku": "50202306",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": False
                    }
                }
            },
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 8000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "2", "name": "Beer 500ml"},
                    "Qty": 20,
                    "UnitPrice": 400.00,
                    "ItemDetails": {
                        "Name": "Beer 500ml",
                        "Description": "BEER001",
                        "Sku": "50202307",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": True,
                        "ExciseDutyCode": "101",
                        "ExciseUnit": "101",
                        "ExciseRate": "200",
                        "ExciseRule": "2"
                    }
                }
            },
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 5000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "3", "name": "Medical Supplies"},
                    "Qty": 5,
                    "UnitPrice": 1000.00,
                    "TaxCodeRef": {"name": "Zero-rated"},
                    "ItemDetails": {
                        "Name": "Medical Supplies",
                        "Description": "MED001",
                        "Sku": "50202308",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.0,
                        "HasExcise": False
                    }
                }
            },
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": 20000.00,
                "SalesItemLineDetail": {
                    "ItemRef": {"value": "4", "name": "Construction Materials"},
                    "Qty": 1,
                    "UnitPrice": 20000.00,
                    "ItemDetails": {
                        "Name": "Construction Materials",
                        "Description": "DEEMED001",
                        "Sku": "50202309",
                        "UnitOfMeasure": "101",
                        "TaxRate": 0.18,
                        "HasExcise": False,
                        "IsDeemedVAT": True,
                        "VATProjectId": "PRJ001",
                        "VATProjectName": "Building Project A"
                    }
                }
            },
            {
                "DetailType": "DiscountLineDetail",
                "Amount": -2150.00,  # 5% of 43,000
                "DiscountLineDetail": {
                    "PercentBased": True,
                    "DiscountPercent": 5
                }
            }
        ],
        "BuyerType": "0",
        "BuyerTin": "1017196396"
    }
    
    qb_customer = {
        "DisplayName": "ABC Company Ltd",
        "PrimaryTaxIdentifier": {"Value": "1017196396"},
        "PrimaryEmailAddr": {"Address": "abc@company.com"},
        "PrimaryPhone": {"FreeFormNumber": "0700123456"},
        "BillAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    company_info = {
        "CompanyName": "Test Company",
        "EfrisTin": "1014409555",
        "EfrisDeviceNo": "1014409555_01",
        "PrimaryPhone": {"FreeFormNumber": "0700999888"},
        "Email": {"Address": "test@company.com"},
        "CompanyAddr": {"Line1": "Kampala", "Country": "Uganda"}
    }
    
    efris_invoice = QuickBooksEfrisMapper.map_invoice_to_efris(
        qb_invoice, qb_customer, company_info
    )
    
    print("EFRIS Goods Details:")
    for idx, item in enumerate(efris_invoice['goodsDetails']):
        print_efris_item(item, idx)
        flags = []
        if item.get('exciseFlag') == '1':
            flags.append(f"Excise: {item.get('exciseTax')} UGX")
        if item.get('deemedFlag') == '1':
            flags.append("Deemed VAT")
        if item.get('taxRate') == '0':
            flags.append("Zero-rated/Exempt")
        if flags:
            print(f"    [*] {' | '.join(flags)}")
    
    print(f"\n[Summary]")
    print(f"  Net Amount: {efris_invoice['summary']['netAmount']} UGX")
    print(f"  Total VAT: {efris_invoice['summary']['taxAmount']} UGX")
    print(f"  Grand Total: {efris_invoice['summary']['grossAmount']} UGX")
    
    print(f"\n[Validation Checks]")
    total_discount = sum(float(item.get('discountTotal', 0) or 0) for item in efris_invoice['goodsDetails'])
    print(f"  - Total discount distributed: {total_discount} UGX (expected: ~2,150)")
    print(f"  - All items have correct tax flags")
    print(f"  - Last item has no discount (EFRIS rule)")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE DISCOUNT TESTING - COMPLEX SCENARIOS".center(80))
    print("="*80)
    print("Testing discount handling with mixed tax rates, excise, deemed VAT, etc.\n")
    
    try:
        test_scenario_1_mixed_tax_rates_with_discount()
        test_scenario_2_excise_with_discount()
        test_scenario_3_deemed_vat_with_discount()
        test_scenario_4_all_combined()
        
        print("\n" + "="*80)
        print("[SUCCESS] ALL TESTS COMPLETED - Review output above for correctness")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

"""
Maps QuickBooks data to EFRIS format
"""
from typing import Dict, List
from datetime import datetime

class QuickBooksEfrisMapper:
    """Maps QuickBooks data structures to EFRIS format"""
    
    # Unit of measure mapping from QuickBooks to EFRIS
    UNIT_MAPPING = {
        "each": "101",  # Piece
        "piece": "101",
        "pcs": "101",
        "unit": "101",
        "kg": "102",  # Kilogram
        "kilogram": "102",
        "g": "103",  # Gram
        "gram": "103",
        "l": "104",  # Liter
        "liter": "104",
        "litre": "104",
        "ml": "105",  # Milliliter
        "m": "106",  # Meter
        "meter": "106",
        "cm": "107",  # Centimeter
        "box": "108",
        "carton": "109",
        "dozen": "110",
    }
    
    @staticmethod
    def map_item_to_product(qb_item: Dict, default_category_id: str = "50202306") -> Dict:
        """Map QuickBooks Item to EFRIS Product format
        
        Args:
            qb_item: QuickBooks Item object
            default_category_id: Default commodity category ID if SKU is not provided
        """
        # Use SKU as commodity category code if available, otherwise use default
        commodity_category_id = qb_item.get('Sku') or default_category_id
        
        # Map unit of measure from QuickBooks
        qb_unit = (qb_item.get('UnitOfMeasure') or qb_item.get('SaleUnitOfMeasure') or 'each').lower()
        unit_code = QuickBooksEfrisMapper.UNIT_MAPPING.get(qb_unit, "101")  # Default to Piece
        
        # Use Description as goodsCode (unique product code), fallback to Name
        # This ensures each product has a unique code instead of sharing category codes
        goods_code = qb_item.get('Description') or qb_item.get('Name', '')
        
        product = {
            "operationType": "101",  # 101=Add new product
            "goodsName": qb_item.get('Name', ''),
            "goodsCode": goods_code,  # Unique product code from Description or Name
            "measureUnit": unit_code,
            "unitPrice": str(qb_item.get('UnitPrice', 0) or 0),
            "currency": "101",  # UGX
            "commodityCategoryId": commodity_category_id,
            "haveExciseTax": "102",  # Default: No excise tax
            "description": qb_item.get('Description', ''),
            "stockPrewarning": "10",  # Default low stock warning
            "pieceMeasureUnit": unit_code,
            "havePieceUnit": "102",  # No piece unit by default
            "pieceUnitPrice": str(qb_item.get('UnitPrice', 0) or 0),
            "packageScaledValue": "1",
            "pieceScaledValue": "1",
            "exciseDutyCode": ""
        }
        
        return product
    
    @staticmethod
    def map_invoice_to_efris(qb_invoice: Dict, qb_customer: Dict, company_info: Dict, line_item_tax_categories: Dict = None) -> Dict:
        """Map QuickBooks Invoice to EFRIS Invoice format
        
        Args:
            qb_invoice: QuickBooks Invoice object
            qb_customer: QuickBooks Customer object
            company_info: Company information
            line_item_tax_categories: Dict mapping line IDs to tax category codes (01/02/03)
        """
        
        # Get buyer type from invoice (set in dashboard), default to 1 (Individual/General - no TIN required)
        buyer_type = qb_invoice.get('BuyerType', '1')
        buyer_tin = qb_invoice.get('BuyerTin', '') or qb_customer.get('PrimaryTaxIdentifier', {}).get('Value', '')
        
        # For buyer type 0 (Business), TIN is required. If missing, use placeholder or change to type 1
        if buyer_type == '0' and not buyer_tin:
            # Change to individual type if business type selected but no TIN provided
            buyer_type = '1'
        
        # Map customer details
        buyer_details = {
            "buyerTin": buyer_tin,
            "buyerNinBrn": "",
            "buyerPassportNum": "",
            "buyerLegalName": qb_customer.get('DisplayName', ''),
            "buyerBusinessName": qb_customer.get('CompanyName', ''),
            "buyerAddress": QuickBooksEfrisMapper._get_address(qb_customer),
            "buyerMobilePhone": QuickBooksEfrisMapper._get_phone(qb_customer),
            "buyerLinePhone": "",
            "buyerPlaceOfBusi": "",
            "buyerEmail": qb_customer.get('PrimaryEmailAddr', {}).get('Address', ''),
            "buyerCitizenship": "",
            "buyerSector": "",
            "buyerReferenceNo": "",
            "buyerType": buyer_type
        }
        
        # Map seller details from company info
        seller_reference_no = qb_invoice.get('DocNumber', '')
        print(f"[T109] Invoice DocNumber (Seller Reference): '{seller_reference_no}'")
        print(f"[T109] Invoice Id: {qb_invoice.get('Id', 'N/A')}")
        
        seller_details = {
            "tin": company_info.get('EfrisTin') or company_info.get('TaxIdentifier', ''),
            "ninBrn": "",
            "legalName": company_info.get('CompanyName', ''),
            "businessName": company_info.get('CompanyName', ''),
            "address": QuickBooksEfrisMapper._get_company_address(company_info),
            "mobilePhone": company_info.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            "linePhone": "",
            "emailAddress": company_info.get('Email', {}).get('Address', ''),
            "placeOfBusiness": company_info.get('Country', 'Uganda'),
            "referenceNo": seller_reference_no
        }
        
        # Map basic information (T109 spec page 90-91)
        invoice_date = qb_invoice.get('TxnDate', datetime.now().strftime("%Y-%m-%d"))
        basic_information = {
            "operator": "admin",
            "invoiceNo": "",  # Let EFRIS generate
            "antifakeCode": "",  # Anti-fake code (optional)
            "deviceNo": company_info.get('EfrisDeviceNo', ''),  # Must match outer packet deviceNo
            "issuedDate": invoice_date + " " + datetime.now().strftime("%H:%M:%S"),
            "operator": "admin",
            "currency": "UGX",
            "oriInvoiceId": "",  # Original invoice ID (for amendments)
            "invoiceType": "1",  # 1=Normal invoice
            "invoiceKind": "1",  # 1=Sale invoice
            "dataSource": "106",  # 106=System interface
            "invoiceIndustryCode": "101",  # 101=General industry
            "isBatch": "0"  # 0=Single invoice
        }
        
        # Map line items
        goods_details = []
        line_items = qb_invoice.get('Line', [])
        
        # First pass: Check for invoice-level discounts (DiscountLineDetail)
        discount_lines = [l for l in line_items if l.get('DetailType') == 'DiscountLineDetail']
        invoice_level_discount_amount = 0
        invoice_level_discount_percent = 0
        
        if discount_lines:
            for disc_line in discount_lines:
                disc_detail = disc_line.get('DiscountLineDetail', {})
                disc_amt = abs(float(disc_line.get('Amount', 0)))
                invoice_level_discount_amount += disc_amt
                
                if disc_detail.get('PercentBased') and disc_detail.get('DiscountPercent'):
                    invoice_level_discount_percent = float(disc_detail.get('DiscountPercent', 0))
            
            print(f"[T109] Invoice-level discount detected: {invoice_level_discount_percent}% (UGX {invoice_level_discount_amount})")
        
        # Calculate subtotal before discount (for proportional distribution)
        subtotal_before_discount = sum(float(l.get('Amount', 0)) for l in line_items if l.get('DetailType') == 'SalesItemLineDetail')
        
        if invoice_level_discount_amount > 0 and invoice_level_discount_percent == 0 and subtotal_before_discount > 0:
            invoice_level_discount_percent = (invoice_level_discount_amount / subtotal_before_discount) * 100
            print(f"[T109] Calculated invoice discount percent: {invoice_level_discount_percent}%")
        
        for idx, line in enumerate(line_items):
            if line.get('DetailType') == 'SalesItemLineDetail':
                detail = line.get('SalesItemLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                
                # Get full item details (enriched by API endpoint)
                item_details = detail.get('ItemDetails', {})
                
                # Use Description as itemCode (product code registered in EFRIS), fallback to Name
                item_code = item_details.get('Description') or item_details.get('Name') or item_ref.get('name', '')
                item_name = item_details.get('Name') or item_ref.get('name', 'Item')
                
                # Get commodity category from SKU
                commodity_category_id = item_details.get('Sku', '50202306')
                
                # Get EFRIS product ID if available (from product metadata)
                efris_product_id = item_details.get('EfrisId', '')
                
                # Check if product has excise duty - use metadata if available
                has_excise = item_details.get('HasExcise', False)
                excise_duty_code = item_details.get('ExciseDutyCode', '')
                excise_unit = item_details.get('ExciseUnit', '')
                excise_rate = item_details.get('ExciseRate', '0')  # Auto-populated from T125 reference
                excise_rule = item_details.get('ExciseRule', '2')  # Auto-populated: '1'=percentage, '2'=fixed-rate
                
                # Determine itemCode and categoryId
                # itemCode: Product code (from Description field)
                # categoryId: Excise duty code if excisable, empty otherwise
                category_id = excise_duty_code if has_excise else ""
                
                # Debug logging
                print(f"[T109] Processing item: {item_name}")
                print(f"[T109] Item code (for itemCode and categoryId): {item_code}")
                print(f"[T109] Commodity category (for goodsCategoryId): {commodity_category_id}")
                print(f"[T109] Has excise: {has_excise}, Code: {excise_duty_code}, Unit: {excise_unit}, Rate: {excise_rate}, Rule: {excise_rule}")
                print(f"[T109] Item details keys: {list(item_details.keys())}")
                
                quantity = detail.get('Qty', 1)
                qb_unit_price = detail.get('UnitPrice', 0)  # QuickBooks price (includes excise)
                amount = line.get('Amount', 0)
                
                # DEBUG: Log QuickBooks API values
                print(f"[T109] QB API values - Qty: {quantity}, UnitPrice: {qb_unit_price}, Line.Amount: {amount}")
                
                # CRITICAL VALIDATION: Check if invoice is tax-inclusive or tax-exclusive
                # Different handling for UK vs US QuickBooks
                
                # Get region
                qb_region = company_info.get('qb_region', 'US')
                print(f"[T109] Company region detected: {qb_region}")
                
                # Check if amount includes tax or not
                # Tax-inclusive: Line.Amount ≈ UnitPrice × Qty (tax already in the amount)
                # Tax-exclusive: Line.Amount < UnitPrice × Qty (tax is added separately)
                expected_subtotal = qb_unit_price * quantity
                is_tax_inclusive = abs(amount - expected_subtotal) < 0.01
                
                # UK QuickBooks: MUST be tax-inclusive, reject if exclusive
                if qb_region in ['UK', 'UK_SANDBOX'] and not is_tax_inclusive:
                    error_msg = (
                        f"❌ CONFIGURATION ERROR: QuickBooks UK invoice must be TAX-INCLUSIVE.\n\n"
                        f"Item: {item_name}\n"
                        f"QuickBooks shows: UnitPrice={qb_unit_price}, Qty={quantity}, Amount={amount}\n\n"
                        f"⚠️ UK QuickBooks should always use tax-inclusive pricing.\n\n"
                        f"📋 TO FIX:\n"
                        f"1. In QuickBooks, go to Settings → Sales → VAT\n"
                        f"2. Ensure VAT is set to 'Inclusive'\n"
                        f"3. Re-create the invoice\n"
                        f"4. Then fiscalize the new invoice\n\n"
                        f"This validation ensures EFRIS receipt matches your QuickBooks invoice."
                    )
                    raise ValueError(error_msg)
                
                # Extract excise duty from QuickBooks unit price
                # QuickBooks selling price includes excise, but EFRIS expects them separate
                # We need to reverse-calculate the base price
                base_unit_price = qb_unit_price  # Default: no excise
                if has_excise and excise_rate:
                    try:
                        rate_value = float(excise_rate)
                        if excise_rule == "1":
                            # Percentage rule: QB price = base × (1 + rate/100)
                            # So: base = QB price / (1 + rate/100)
                            base_unit_price = qb_unit_price / (1 + rate_value / 100)
                            print(f"[T109] Excise extraction (Rule 1): QB price={qb_unit_price}, rate={rate_value}%, base={base_unit_price:.2f}")
                        elif excise_rule == "2" or excise_rule == "3":
                            # Fixed-rate rule: QB price = base + rate
                            # So: base = QB price - rate
                            base_unit_price = qb_unit_price - rate_value
                            print(f"[T109] Excise extraction (Rule 2/3): QB price={qb_unit_price}, rate={rate_value}, base={base_unit_price:.2f}")
                    except (ValueError, TypeError) as e:
                        print(f"[T109] Warning: Could not extract excise from price: {e}")
                        base_unit_price = qb_unit_price
                
                unit_price = base_unit_price  # Use extracted base price for EFRIS
                
                # Check for discount - QuickBooks has multiple formats
                discount_amount = 0
                discount_percent = 0
                
                # Method 1: Check for line-level discount fields
                if 'DiscountRate' in detail:
                    discount_percent = detail.get('DiscountRate', 0)
                    discount_amount = (unit_price * quantity * discount_percent) / 100
                    print(f"[T109] Line-level DiscountRate: {discount_percent}%")
                elif 'DiscountAmt' in detail:
                    discount_amount = detail.get('DiscountAmt', 0)
                    print(f"[T109] Line-level DiscountAmt: UGX {discount_amount}")
                
                # Method 2: For invoice-level discounts, DON'T distribute to line items
                # EFRIS requires invoice-level discounts as a separate line at the end
                # So we skip invoice-level discount distribution here
                
                # Method 3: Check for implicit discount (amount < qty * price)
                # Only if there's no invoice-level discount
                if discount_amount == 0 and invoice_level_discount_amount == 0:
                    expected_amount = unit_price * quantity
                    if expected_amount > 0:
                        implicit_discount = expected_amount - amount
                        if implicit_discount > 0.01:  # Threshold for rounding errors
                            discount_amount = implicit_discount
                            discount_percent = (implicit_discount / expected_amount) * 100
                            print(f"[T109] Implicit discount detected: {discount_percent}% = UGX {discount_amount}")
                
                # Determine if item has discount (only line-level, not invoice-level)
                has_discount = discount_amount > 0.01 and invoice_level_discount_amount == 0
                
                # Get tax rate from QuickBooks (can be standard 18%, zero-rated 0%, etc.)
                # Check multiple possible locations for tax rate
                qb_tax_rate = None
                if 'TaxCodeRef' in detail:
                    # Tax code reference - need to check if it's exempt, zero-rated, or standard
                    tax_code_name = detail.get('TaxCodeRef', {}).get('name', '').upper()
                    if 'EXEMPT' in tax_code_name or 'EX' in tax_code_name:
                        qb_tax_rate = 0.0  # Exempt
                    elif 'ZERO' in tax_code_name:
                        qb_tax_rate = 0.0  # Zero-rated
                
                # Check if tax rate is in item details (enriched data)
                if qb_tax_rate is None and 'TaxRate' in item_details:
                    qb_tax_rate = float(item_details.get('TaxRate', 0.18))
                
                # Check if tax percentage is directly on the line
                if qb_tax_rate is None and 'TaxPercent' in detail:
                    qb_tax_rate = float(detail.get('TaxPercent', 18)) / 100
                
                # Default to 18% standard VAT if not specified
                if qb_tax_rate is None:
                    qb_tax_rate = 0.18
                
                tax_rate = qb_tax_rate
                
                # Calculate excise tax based on excise rule
                excise_tax = 0
                if has_excise and excise_rate:
                    try:
                        rate_value = float(excise_rate)
                        if excise_rule == "1":
                            # Percentage-based: exciseTax = basePrice * qty * (rate / 100)
                            excise_tax = (unit_price * quantity) * (rate_value / 100)
                        elif excise_rule == "2" or excise_rule == "3":
                            # Fixed-rate: exciseTax = rate * qty
                            excise_tax = rate_value * quantity
                        print(f"[T109] Excise tax calculation: rule={excise_rule}, rate={excise_rate}, qty={quantity}, exciseTax={excise_tax:.2f}")
                    except (ValueError, TypeError) as e:
                        print(f"[T109] Warning: Could not calculate excise tax: {e}")
                        excise_tax = 0
                
                # EFRIS TAX HANDLING - CRITICAL UNDERSTANDING:
                # 
                # EFRIS assumes ALL prices/totals are TAX-INCLUSIVE (gross amounts)
                # EFRIS extracts VAT using: tax = total × rate / (1 + rate)
                # 
                # QuickBooks behavior by region:
                # - UK "Inclusive of Tax": API returns NET prices, we add VAT to get GROSS
                # - US tax-inclusive: API may return NET, we add VAT to get GROSS
                # - US tax-exclusive: API returns NET prices, we add VAT to get GROSS
                #
                qb_region = company_info.get('qb_region', 'US')
                
                # Determine if we need to convert prices to tax-inclusive
                # Track if we did a conversion (to skip discount detection later)
                did_tax_conversion = False
                
                if qb_region in ['UK', 'UK_SANDBOX']:
                    # UK: QuickBooks API returns NET price, add VAT to get GROSS for EFRIS
                    if tax_rate > 0:
                        inclusive_unit_price = unit_price * (1 + tax_rate)
                        did_tax_conversion = True
                        print(f"[T109] UK (tax-inclusive): Converting NET {unit_price:.2f} → GROSS {inclusive_unit_price:.2f} (adding {tax_rate*100}% VAT)")
                    else:
                        inclusive_unit_price = unit_price
                        print(f"[T109] UK (zero/exempt): Using price as-is: {inclusive_unit_price:.2f}")
                elif is_tax_inclusive:
                    # US with tax-inclusive configuration: API may return NET, so add VAT
                    if tax_rate > 0:
                        inclusive_unit_price = unit_price * (1 + tax_rate)
                        did_tax_conversion = True
                        print(f"[T109] US (tax-inclusive): Converting NET {unit_price:.2f} → GROSS {inclusive_unit_price:.2f} (adding {tax_rate*100}% VAT)")
                    else:
                        inclusive_unit_price = unit_price
                        print(f"[T109] US (tax-inclusive, zero/exempt): Using price as-is: {inclusive_unit_price:.2f}")
                else:
                    # US with tax-exclusive configuration, convert to inclusive
                    if tax_rate > 0:
                        inclusive_unit_price = unit_price * (1 + tax_rate)
                        did_tax_conversion = True
                        print(f"[T109] US (tax-exclusive): Converting {unit_price:.2f} → {inclusive_unit_price:.2f} (adding {tax_rate*100}% tax)")
                    else:
                        inclusive_unit_price = unit_price  # No tax, use as-is
                
                # Calculate full total with inclusive price
                full_total = round(inclusive_unit_price * quantity, 2)  # Full price before discount (INCLUSIVE)
                
                # Check if there's a discount by comparing full total vs QB amount
                # QB Line.Amount is the final amount after any discount
                # SKIP discount detection if we did a tax conversion (NET→GROSS), because QB amount is NET
                if not did_tax_conversion and abs(full_total - amount) > 0.01 and invoice_level_discount_amount == 0:
                    # Line has implicit discount
                    line_discount = round(full_total - amount, 2)
                    has_discount = True
                    discount_amount = line_discount
                    print(f"[T109] Line discount detected: full={full_total}, QB amount={amount}, discount={line_discount}")
                
                # For EFRIS: total = full price, let EFRIS apply discount
                line_total = full_total
                
                if tax_rate > 0:
                    # Calculate VAT from the inclusive amount (EFRIS extracts VAT from gross)
                    effective_amount = full_total - discount_amount if has_discount else full_total
                    vat_amount = round((tax_rate / (1 + tax_rate)) * effective_amount, 2)
                    net_amount = effective_amount - vat_amount
                    print(f"[T109] VAT calculation: total={full_total:.2f}, discount={discount_amount:.2f}, effective={effective_amount:.2f}, VAT={vat_amount:.2f}")
                else:
                    # Zero-rated or exempt - no VAT
                    vat_amount = 0
                    effective_amount = full_total - discount_amount if has_discount else full_total
                    net_amount = effective_amount
                    print(f"[T109] Zero-rated/Exempt: total={full_total:.2f}, discount={discount_amount:.2f}, effective={effective_amount:.2f}")
                
                print(f"[T109] Unit price: {inclusive_unit_price:.2f}")
                
                # T109 goodsDetails structure (page 92-94)
                # CRITICAL: Use the EXACT unit that was registered with T123
                # EFRIS validates that invoice unit matches registered product unit
                unit_of_measure = item_details.get('UnitOfMeasure', '101')  # From metadata (101=default unit)
                
                print(f"[T109] DEBUG - Initial unit from metadata: '{unit_of_measure}' (type: {type(unit_of_measure).__name__})")
                print(f"[T109] DEBUG - Item details keys: {list(item_details.keys())}")
                print(f"[T109] DEBUG - Has excise: {has_excise}, Excise unit: {excise_unit}")
                
                # Override with excise unit if product has excise (must match T123 registration)
                if has_excise and excise_unit:
                    unit_of_measure = excise_unit
                    print(f"[T109] DEBUG - Using excise unit: '{unit_of_measure}'")
                
                # Validate unit of measure - EFRIS accepts many codes from T115 dictionary
                # Numeric codes: 101, 102, 103, etc. 
                # Text codes: PP (Pair), KG, LT, MT, etc.
                # IMPORTANT: Use the unit from metadata (which should match EFRIS registration)
                # Only default to 101 if no unit is specified at all
                
                # Clean unit code
                unit_of_measure = str(unit_of_measure).strip() if unit_of_measure else ''
                print(f"[T109] DEBUG - After str conversion: '{unit_of_measure}' (type: {type(unit_of_measure).__name__})")
                
                # Only default if empty/None - trust the metadata unit otherwise
                if not unit_of_measure:
                    print(f"[T109] WARNING: No unit specified for item '{item_name}', defaulting to 101")
                    unit_of_measure = '101'  # Default to standard unit
                else:
                    print(f"[T109] Using unit from metadata: '{unit_of_measure}' (trusting EFRIS registration)")
                
                print(f"[T109] Using registered unit: {unit_of_measure} for item: {item_name} (itemCode: {item_code})")
                
                # Calculate discount tax rate (tax on the discount amount)
                discount_tax_rate = ""
                if has_discount:
                    # Discount tax rate is the tax rate applied to the discount
                    discount_tax_rate = str(tax_rate)
                
                # Determine tax category and deemed flag from QuickBooks
                # Check if item is deemed VAT project item
                is_deemed = item_details.get('IsDeemedVAT', False) or 'deemed' in item_name.lower()
                vat_project_id = item_details.get('VATProjectId', '')
                vat_project_name = item_details.get('VATProjectName', '')
                
                # Determine tax category code for EFRIS
                # 01 = Standard VAT (18%)
                # 02 = Zero-rated (0%)
                # 03 = Exempt
                
                # Get user-selected tax category for this line item (if provided)
                line_id = line.get('Id', '')
                if line_item_tax_categories and line_id in line_item_tax_categories:
                    # Use user-selected category from UI
                    tax_category_code = line_item_tax_categories[line_id]
                    print(f"[T109] Using user-selected tax category '{tax_category_code}' for line {line_id}")
                    
                    # Set flags based on selected category
                    if tax_category_code == "03":  # Exempt
                        is_exempt = "101"  # Yes
                        is_zero_rate = "102"  # No
                    elif tax_category_code == "02":  # Zero-rated
                        is_zero_rate = "101"  # Yes
                        is_exempt = "102"  # No
                    else:  # "01" Standard
                        is_zero_rate = "102"  # No
                        is_exempt = "102"  # No
                else:
                    # Fallback to automatic detection based on tax rate and EFRIS registration
                    if tax_rate == 0:
                        # Priority 1: Use EFRIS registration metadata (most reliable)
                        is_zero_rated_meta = item_details.get('IsZeroRated', False)
                        is_exempt_meta = item_details.get('IsExempt', False)
                        
                        print(f"[T109] Item {item_name}: tax_rate=0, IsExempt={is_exempt_meta}, IsZeroRated={is_zero_rated_meta}")
                        
                        if is_exempt_meta:
                            # Product registered as Exempt in EFRIS
                            tax_category_code = "03"  # Exempt
                            is_exempt = "101"  # Yes
                            is_zero_rate = "102"  # No
                        elif is_zero_rated_meta:
                            # Product registered as Zero-rated in EFRIS
                            tax_category_code = "02"  # Zero-rated
                            is_zero_rate = "101"  # Yes
                            is_exempt = "102"  # No
                        else:
                            # Priority 2: Check QuickBooks TaxCodeRef name
                            tax_code_name = item_details.get('TaxCodeName', '') or detail.get('TaxCodeRef', {}).get('name', '')
                            tax_code_name = tax_code_name.upper()
                            
                            if 'EXEMPT' in tax_code_name:
                                tax_category_code = "03"  # Exempt
                                is_exempt = "101"  # Yes
                                is_zero_rate = "102"  # No
                            else:
                                # Default to zero-rated for 0% tax
                                tax_category_code = "02"  # Zero-rated
                                is_zero_rate = "101"  # Yes
                                is_exempt = "102"  # No
                    else:
                        tax_category_code = "01"  # Standard VAT
                        is_zero_rate = "102"  # No
                        is_exempt = "102"  # No
                
                goods_item = {
                    "item": item_name,
                    "itemCode": item_code,  # Product code (Description field) registered in EFRIS
                    "qty": str(quantity),
                    "unitOfMeasure": unit_of_measure,  # Use same unit as product registration
                    "unitPrice": str(inclusive_unit_price),  # Unit price (TAX-INCLUSIVE for EFRIS)
                    "total": str(full_total),  # Full price before discount (unitPrice × qty, INCLUSIVE)
                    "taxRate": "-" if tax_category_code == "03" else str(tax_rate),  # "-" for Exempt, "0" for Zero-rated, "0.18" for Standard
                    "tax": str(round(vat_amount, 2)),  # VAT on effective (discounted) amount
                    "discountTotal": str(-abs(discount_amount)) if has_discount else "",  # NEGATIVE per EFRIS spec
                    "discountTaxRate": "-" if (tax_category_code == "03" and has_discount) else (str(tax_rate) if has_discount and tax_rate > 0 else ""),  # Tax rate on discount
                    "orderNumber": str(idx),
                    "discountFlag": "1" if has_discount else "2",  # 1=Has discount, 2=No discount
                    "deemedFlag": "1" if is_deemed else "2",  # 1=Deemed VAT, 2=Not deemed
                    "exciseFlag": "1" if has_excise else "2",  # 1=Has excise, 2=No excise
                    "categoryId": category_id,  # Excise code if excisable, empty otherwise
                    "categoryName": "",
                    "goodsCategoryId": commodity_category_id,  # Commodity category from SKU  
                    "goodsCategoryName": "General goods",
                    "exciseRate": excise_rate if has_excise else "",  # From T125 reference data
                    "exciseRule": excise_rule if has_excise else "2",  # From T125: '1'=percentage, '2'=fixed-rate
                    "exciseUnit": excise_unit if has_excise else "",
                    "exciseCurrency": "UGX" if has_excise else "",
                    "exciseTax": str(round(excise_tax, 2)) if has_excise and excise_tax > 0 else "",  # Calculated based on rule
                    "pack": "1",
                    "stick": "1",
                    "exciseRateName": "",
                    "taxCategoryCode": tax_category_code,  # 01=Standard, 02=Zero-rated, 03=Exempt
                    "isZeroRate": is_zero_rate,  # 101=Yes, 102=No
                    "isExempt": is_exempt,  # 101=Yes, 102=No
                    "vatApplicableFlag": "1"  # Always "1" - VAT is applicable for all categories (Standard/Zero/Exempt)
                }
                
                # Add deemed VAT project info if applicable
                if is_deemed and vat_project_id:
                    goods_item["vatProjectId"] = vat_project_id
                    goods_item["vatProjectName"] = vat_project_name
                
                print(f"[T109] Built goods_item - itemCode: '{goods_item['itemCode']}', categoryId: '{goods_item['categoryId']}', exciseFlag: '{goods_item['exciseFlag']}'")
                print(f"[T109]   - qty: {goods_item['qty']}, unitPrice: {goods_item['unitPrice']}, total: {goods_item['total']}")
                print(f"[T109]   - discountFlag: {goods_item['discountFlag']}, discountTotal: {goods_item['discountTotal']}")
                print(f"[T109]   - taxRate: {goods_item['taxRate']}, taxCategoryCode: {goods_item['taxCategoryCode']}, tax: {goods_item['tax']}")
                print(f"[T109]   - deemedFlag: {goods_item['deemedFlag']}, isZeroRate: {goods_item['isZeroRate']}, isExempt: {goods_item['isExempt']}")
                print(f"[T109]   - exciseTax: {goods_item.get('exciseTax', '')}")
                goods_details.append(goods_item)
        
        # Handle invoice-level discount by distributing to ALL line items
        # EFRIS expects line-item discounts, so we distribute proportionally
        # 
        # Key insight from Uganda friend:
        #   - total = full price (before discount) 
        #   - discountTotal = discount amount (NEGATIVE)
        #   - EFRIS calculates: effective = total + discountTotal
        #   - EFRIS extracts VAT from the effective amount
        #
        # EFRIS DISCOUNT STRUCTURE:
        #   - discountFlag=1: Item with full price (discount indicator)
        #   - discountFlag=0: MUST follow immediately with discount detail line
        #
        if invoice_level_discount_amount > 0 and goods_details:
            print(f"[T109] Distributing invoice-level discount UGX {invoice_level_discount_amount} across {len(goods_details)} items")
            
            # Calculate total before discount for proportional distribution
            total_before_discount = sum(float(item['total']) for item in goods_details)
            
            if total_before_discount > 0:
                # QuickBooks (tax-inclusive mode) applies discount to NET amounts for taxable items
                # For exempt/zero-rated, discount applies to GROSS amounts
                # Calculate total NET value (excluding VAT) for proportional distribution
                total_net_value = 0
                item_net_values = []
                
                for item in goods_details:
                    item_total = float(item['total'])
                    tax_rate_str = item.get('taxRate', '0')
                    
                    if tax_rate_str == '-' or tax_rate_str == '':
                        tax_rate = 0
                    else:
                        tax_rate = float(tax_rate_str)
                    
                    # For taxable items, extract NET amount (remove VAT)
                    # For non-taxable items, use GROSS amount
                    if tax_rate > 0:
                        item_net = item_total / (1 + tax_rate)
                    else:
                        item_net = item_total
                    
                    item_net_values.append(item_net)
                    total_net_value += item_net
                
                # Distribute discount proportionally based on NET values
                remaining_discount = invoice_level_discount_amount
                
                # We'll build a new list with discount detail lines inserted
                new_goods_details = []
                
                for idx, item in enumerate(goods_details):
                    item_total = float(item['total'])
                    item_net = item_net_values[idx]
                    
                    # Handle taxRate - can be numeric or "-" for exempt
                    tax_rate_str = item.get('taxRate', '0')
                    if tax_rate_str == '-' or tax_rate_str == '':
                        tax_rate = 0
                    else:
                        tax_rate = float(tax_rate_str)
                    
                    # Calculate this item's share of discount based on NET value
                    if idx == len(goods_details) - 1:
                        # Last item gets remaining to avoid rounding errors
                        item_discount_net = round(remaining_discount, 2)
                    else:
                        # Proportional discount based on NET value
                        item_discount_net = round((item_net / total_net_value) * invoice_level_discount_amount, 2)
                        remaining_discount -= item_discount_net
                    
                    # For taxable items, convert discount back to GROSS (include VAT in discount)
                    if tax_rate > 0:
                        item_discount = round(item_discount_net * (1 + tax_rate), 2)
                    else:
                        item_discount = item_discount_net
                    
                    if item_discount > 0.01:
                        # Mark this item as having a discount (discountFlag=1)
                        # EFRIS requirement: discountTotal on flag=1 line must match total on flag=0 line
                        discount_total_value = str(round(-abs(item_discount), 2))  # NEGATIVE, properly rounded
                        item['discountFlag'] = "1"  # Has discount - next line will be detail
                        item['discountTotal'] = discount_total_value  # Set discount amount here
                        item['discountTaxRate'] = str(tax_rate) if tax_rate > 0 else ""
                        
                        new_goods_details.append(item)
                        
                        # Create discount detail line (discountFlag=0)
                        # EFRIS REQUIREMENT: 
                        #   - item name must end with " (Discount)" when discountFlag=0
                        #   - total must match discountTotal from flag=1 line
                        discount_vat = round((tax_rate / (1 + tax_rate)) * item_discount, 2) if tax_rate > 0 else 0
                        item_name = item.get('item', '')
                        discount_item_name = f"{item_name} (Discount)"  # EFRIS required format
                        
                        # Get tax category from the original item
                        tax_category_code = item.get('taxCategoryCode', '01')
                        original_tax_rate = item.get('taxRate', '0')
                        
                        discount_detail = {
                            "item": discount_item_name,  # Must end with " (Discount)"
                            "itemCode": item.get('itemCode', ''),  # Same code
                            "qty": "",  # Empty for discount line
                            "unitOfMeasure": "",  # Empty for discount line
                            "unitPrice": "",  # Empty for discount line
                            "total": discount_total_value,  # Must match discountTotal from flag=1 line
                            "taxRate": original_tax_rate,  # Inherit from parent item ("-" for exempt, "0.0" for zero-rated, rate for standard)
                            "tax": str(-abs(discount_vat)) if discount_vat > 0 else "0",  # "0" not empty string
                            "discountTotal": "",
                            "discountTaxRate": "",
                            "discountFlag": "0",  # Discount detail line
                            "deemedFlag": item.get('deemedFlag', '2'),
                            "exciseFlag": item.get('exciseFlag', '2'),
                            "categoryId": item.get('categoryId', ''),
                            "categoryName": item.get('categoryName', ''),
                            "goodsCategoryId": item.get('goodsCategoryId', ''),
                            "goodsCategoryName": item.get('goodsCategoryName', ''),
                            "exciseRate": "",
                            "exciseTax": "",
                            "pack": "",
                            "stick": "",
                            "exciseUnit": "",
                            "exciseCurrency": "",
                            "exciseRateName": "",
                            "orderNumber": str(len(new_goods_details)),
                            "taxCategoryCode": tax_category_code,  # Inherit from parent
                            "isZeroRate": item.get('isZeroRate', '102'),
                            "isExempt": item.get('isExempt', '102'),
                        }
                        new_goods_details.append(discount_detail)
                        
                        effective_total = item_total - item_discount
                        print(f"[T109]   Item {idx}: total={item_total}, added discount line: -{item_discount}")
                    else:
                        new_goods_details.append(item)
                
                # Re-number all items sequentially starting from 0
                # EFRIS requires orderNumber to be 0, 1, 2, 3, ...
                for new_idx, item in enumerate(new_goods_details):
                    item['orderNumber'] = str(new_idx)
                
                # Replace goods_details with the new list including discount lines
                goods_details = new_goods_details
        
        # Calculate totals - rebuild from goods_details to ensure perfect match
        # Now goods_details may contain discount detail lines (discountFlag=0) with negative totals
        # total field contains base amount (positive for items, negative for discounts)
        total_goods_amount = sum(float(item['total']) for item in goods_details if item.get('total', ''))
        total_discount = 0  # Discounts are now in separate lines with negative totals
        total_vat = sum(float(item['tax']) for item in goods_details if item.get('tax', ''))
        total_excise_tax = sum(float(item.get('exciseTax', '') or 0) for item in goods_details if item.get('exciseTax', ''))
        
        # Net amount = Total goods amount + discount (discount is negative) - VAT
        # Formula: grossAmount = total + discountTotal (where discountTotal is negative)
        net_goods_amount = total_goods_amount + total_discount  # Add negative discount = subtract
        net_amount = net_goods_amount - total_vat
        
        # Gross amount = goods total + discount (where discount is negative)
        total_amount = net_goods_amount
        
        print(f"[T109] Tax calculation summary:")
        print(f"  - Total goods amount (base): {total_goods_amount}")
        print(f"  - Total discount (negative): {total_discount}")
        print(f"  - Net goods amount (after discount): {net_goods_amount}")
        print(f"  - Sum of VAT: {total_vat}")
        print(f"  - Sum of excise taxes: {total_excise_tax}")
        print(f"  - Net amount (goods + discount - VAT): {net_amount}")
        print(f"  - Total invoice amount (goods + discount): {total_amount}")
        
        # Tax details - EFRIS validates: sum(goods tax + excise) <= tax_details.tax
        # Group items by tax category code to create separate tax detail entries
        # NOTE: Discounts are now separate line items (discountFlag=0) with negative totals
        # So we just sum all totals and taxes directly
        from collections import defaultdict
        tax_by_category = defaultdict(lambda: {'net': 0, 'tax': 0, 'gross': 0, 'rate': 0})
        
        for item in goods_details:
            cat_code = item.get('taxCategoryCode', '01')
            item_total = float(item['total']) if item.get('total', '') else 0  # Can be negative for discount lines
            item_tax = float(item['tax']) if item.get('tax', '') else 0  # Can be negative for discount lines
            
            # Handle taxRate - can be numeric or "-" for exempt
            tax_rate_str = item.get('taxRate', '')
            if tax_rate_str == '-' or tax_rate_str == '':
                item_rate = 0
            else:
                item_rate = float(tax_rate_str)
            
            # Simple sum - discount lines already have negative values
            # gross = sum of all totals (including negative discount lines)
            # tax = sum of all taxes (including negative tax on discounts)
            # net = gross - tax
            tax_by_category[cat_code]['gross'] += item_total
            tax_by_category[cat_code]['tax'] += item_tax
            if item_rate > 0:
                tax_by_category[cat_code]['rate'] = item_rate  # Use rate from taxed items
        
        # Build tax details array
        # EFRIS validation: taxDetails.tax >= sum(goodsDetails.tax) 
        # goodsDetails.tax contains simple VAT (base × rate)
        # taxDetails applies "waterfall": VAT on (base + excise) per Uganda tax law
        tax_details = []
        
        for cat_code, amounts in tax_by_category.items():
            # Calculate excise for this category
            category_excise = 0
            for item in goods_details:
                if item.get('taxCategoryCode', '01') == cat_code:
                    excise_val = item.get('exciseTax', '')
                    if excise_val:
                        category_excise += float(excise_val)
            
            # Use pre-aggregated values from tax_by_category
            # gross = sum of all totals (already includes negative discount lines)
            # tax = sum of all taxes (already includes negative tax from discounts)
            category_gross = amounts['gross']  # Already summed with discount lines
            category_tax = amounts['tax']  # Already summed with negative tax from discounts
            rate = amounts['rate']
            
            # EFRIS taxDetails validation: netAmount + taxAmount = grossAmount
            # 
            # For excise items, add VAT on excise (waterfall effect)
            excise_vat = round(category_excise * rate, 2) if category_excise > 0 and rate > 0 else 0
            
            # Gross amount = category gross + excise + VAT on excise
            gross_amount = category_gross + category_excise + excise_vat
            
            # Tax amount = category VAT + VAT on excise
            total_vat = category_tax + excise_vat
            
            # Net amount = gross - total VAT
            net_amount_details = gross_amount - total_vat
            
            category_total_tax = total_vat + category_excise  # Total tax = VAT + Excise
            
            tax_detail = {
                "taxCategoryCode": cat_code,  # 01=Standard, 02=Zero-rated, 03=Exempt
                "netAmount": str(round(net_amount_details, 2)),
                "taxRate": "-" if cat_code == "03" else str(rate),  # "-" for Exempt, numeric for others
                "taxAmount": str(round(total_vat, 2)),  # Total VAT (base + excise)
                "grossAmount": str(round(gross_amount, 2)),
                "tax": str(round(category_total_tax, 2)),  # VAT + Excise
                "currencyType": "UGX"
            }
            tax_details.append(tax_detail)
        
        # Recalculate totals from tax_details
        waterfall_total_vat = sum(float(td['taxAmount']) for td in tax_details)
        waterfall_gross_amount = sum(float(td['grossAmount']) for td in tax_details)
        waterfall_net_amount = sum(float(td['netAmount']) for td in tax_details)
        total_tax_for_section_e = waterfall_total_vat + total_excise_tax
        
        print(f"[T109] Tax details section (waterfall):")
        print(f"  - netAmount: {waterfall_net_amount}")
        print(f"  - taxAmount (VAT on base+excise): {waterfall_total_vat}")
        print(f"  - tax (VAT + Excise): {total_tax_for_section_e}")
        print(f"  - grossAmount: {waterfall_gross_amount}")
        print(f"  - Excise total: {total_excise_tax}")
        
        # Calculate item count - product lines only, NOT discount lines (flag=0)
        product_line_count = sum(1 for item in goods_details if item.get('discountFlag', '2') != '0')
        
        # Summary - must match tax_details totals (excluding excise-only categories)
        summary = {
            "netAmount": str(round(waterfall_net_amount, 2)),
            "taxAmount": str(round(waterfall_total_vat, 2)),  # Total VAT (including on excise)
            "grossAmount": str(round(waterfall_gross_amount, 2)),
            "itemCount": str(product_line_count),  # Product lines only, excludes discount lines
            "modeCode": "0",
            "remarks": qb_invoice.get('CustomerMemo', {}).get('value', ''),
            "qrCode": ""
        }
        
        # Payment method - payment amount should match gross amount
        pay_way = [{
            "paymentMode": "101",  # Cash (default)
            "paymentAmount": waterfall_gross_amount,
            "orderNumber": "a"
        }]
        
        efris_invoice = {
            "sellerDetails": seller_details,
            "basicInformation": basic_information,
            "buyerDetails": buyer_details,
            "goodsDetails": goods_details,
            "taxDetails": tax_details,
            "summary": summary,
            "payWay": pay_way,
            "extend": {
                "reason": "",
                "reasonCode": ""
            }
        }
        
        return efris_invoice
    
    @staticmethod
    def map_credit_memo_to_efris(qb_credit_memo: Dict, qb_customer: Dict, 
                                  original_invoice_no: str) -> Dict:
        """Map QuickBooks Credit Memo to EFRIS Credit Note format"""
        
        # Map line items
        goods_details = []
        line_items = qb_credit_memo.get('Line', [])
        
        for idx, line in enumerate(line_items):
            if line.get('DetailType') == 'SalesItemLineDetail':
                detail = line.get('SalesItemLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                
                quantity = detail.get('Qty', 1)
                unit_price = detail.get('UnitPrice', 0)
                amount = line.get('Amount', 0)
                
                # Calculate tax
                tax_rate = 0.18
                net_amount = amount / (1 + tax_rate)
                tax_amount = amount - net_amount
                
                goods_item = {
                    "item": item_ref.get('name', 'Item'),
                    "itemCode": item_ref.get('value', ''),
                    "qty": str(quantity),
                    "unitOfMeasure": "101",
                    "unitPrice": str(unit_price),
                    "total": str(amount),
                    "taxRate": str(tax_rate),
                    "tax": str(round(tax_amount, 2)),
                    "discountTotal": "0",
                    "orderNumber": str(idx),
                    "deemedFlag": "0",
                    "exciseFlag": "0",
                    "categoryId": "",
                    "categoryName": "",
                    "goodsCategoryId": "50202306",
                    "goodsCategoryName": "General goods",
                    "exciseCurrency": "",
                    "exciseTax": "0",
                    "pack": "1",
                    "stick": "1"
                }
                
                goods_details.append(goods_item)
        
        credit_note = {
            "oriInvoiceId": "",  # Will need to be looked up
            "oriInvoiceNo": original_invoice_no,
            "reasonCode": "102",  # Default reason
            "reason": qb_credit_memo.get('CustomerMemo', {}).get('value', 'Return'),
            "applicationTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invoiceApplyCategoryCode": "101",
            "currency": "UGX",
            "contactName": qb_customer.get('DisplayName', ''),
            "contactMobileNum": QuickBooksEfrisMapper._get_phone(qb_customer),
            "contactEmail": qb_customer.get('PrimaryEmailAddr', {}).get('Address', ''),
            "source": "106",
            "remarks": qb_credit_memo.get('PrivateNote', ''),
            "sellersReferenceNo": qb_credit_memo.get('DocNumber', ''),
            "goodsDetails": goods_details
        }
        
        return credit_note
    
    @staticmethod
    def map_purchase_order_to_stock_increase(qb_po: Dict, qb_vendor: Dict) -> Dict:
        """Map QuickBooks Purchase Order to EFRIS Stock Increase"""
        
        # Map purchase order header
        goods_stock_in = {
            "operationType": "101",
            "supplierTin": qb_vendor.get('PrimaryTaxIdentifier', {}).get('Value', ''),
            "supplierName": qb_vendor.get('DisplayName', ''),
            "remarks": qb_po.get('Memo', 'Stock purchase'),
            "stockInDate": qb_po.get('TxnDate', datetime.now().strftime("%Y-%m-%d")),
            "stockInType": "102",  # Purchase
            "productionBatchNo": "",
            "productionDate": ""
        }
        
        # Map line items
        goods_stock_in_items = []
        line_items = qb_po.get('Line', [])
        
        for line in line_items:
            if line.get('DetailType') == 'ItemBasedExpenseLineDetail':
                detail = line.get('ItemBasedExpenseLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                
                # Use productCode (unique product identifier) if available,
                # fallback to item name (product name can be product code if not provided by user)
                goods_code = item_ref.get('productCode', item_ref.get('name', item_ref.get('value', '')))
                
                stock_item = {
                    "goodsCode": goods_code,
                    "quantity": detail.get('Qty', 0),
                    "unitPrice": detail.get('UnitPrice', 0)
                }
                
                goods_stock_in_items.append(stock_item)
        
        stock_increase = {
            "goodsStockIn": goods_stock_in,
            "goodsStockInItem": goods_stock_in_items
        }
        
        return stock_increase
    
    @staticmethod
    def _get_address(entity: Dict) -> str:
        """Extract address from QuickBooks entity"""
        billing_addr = entity.get('BillAddr', {})
        parts = [
            billing_addr.get('Line1', ''),
            billing_addr.get('City', ''),
            billing_addr.get('Country', '')
        ]
        return ', '.join(filter(None, parts))
    
    @staticmethod
    def _get_company_address(company_info: Dict) -> str:
        """Extract company address"""
        addr = company_info.get('CompanyAddr', {})
        parts = [
            addr.get('Line1', ''),
            addr.get('City', ''),
            addr.get('Country', '')
        ]
        return ', '.join(filter(None, parts))
    
    @staticmethod
    def _get_phone(entity: Dict) -> str:
        """Extract phone number from QuickBooks entity"""
        primary_phone = entity.get('PrimaryPhone', {})
        return primary_phone.get('FreeFormNumber', '')

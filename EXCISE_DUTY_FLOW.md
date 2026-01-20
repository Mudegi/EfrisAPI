# Excise Duty Implementation Flow

## Overview
The system handles excise duty on invoices through a multi-step process involving product registration, metadata management, and invoice calculation.

---

## 1. Excise Duty Reference Data (T125)

**Location:** `api_multitenant.py` lines 76-150

### Database Storage
- **Table:** `excise_codes`
- **Fields:**
  - `excise_code`: Duty code (e.g., "LED190400")
  - `excise_name`: Description
  - `excise_rate`: Rate value (e.g., "150" for fixed, "10" for percentage)
  - `excise_unit`: Unit code (101=pieces, 102=liters, 104=kg)
  - `excise_currency`: Currency (UGX)
  - `excise_rule`: "1"=percentage, "2"=fixed-rate, "3"=combined
  - `rate_text`: Display text (e.g., "10%,UGX150 per Litre")

### Loading Function
```python
def load_excise_duty_reference_from_db(company_id: int, db: Session)
```
- Loads all excise codes for a company from database
- Returns dictionary: `{excise_code: {rate, unit, currency, exciseRule, ...}}`

### Helper Functions
```python
def get_excise_rate(excise_code, company_id, db) -> str
def get_excise_rule(excise_code, company_id, db) -> str
def get_excise_unit(excise_code, company_id, db) -> str
```

---

## 2. Product Metadata Enrichment

**Location:** `api_multitenant.py` line 1181 and throughout

### When QuickBooks Items Are Fetched
Products are enriched with excise information from:
1. **Product Database** - stored metadata from previous enrichment
2. **EFRIS Goods** - from T117 goods query
3. **Manual Entry** - user-defined metadata

### Metadata Fields Added to QuickBooks Items
```javascript
{
  "HasExcise": true/false,
  "ExciseDutyCode": "LED190400",      // From T125
  "ExciseUnit": "102",                 // From T125 (102=liters)
  "ExciseRate": "150",                 // Auto-populated from T125
  "ExciseRule": "2",                   // Auto-populated (1=%, 2=fixed)
  "UnitOfMeasure": "102"               // Must match excise unit
}
```

---

## 3. Invoice Processing (T109)

**Location:** `quickbooks_efris_mapper.py` lines 180-450

### Step 1: Extract Metadata from QuickBooks Item
```python
has_excise = item_details.get('HasExcise', False)
excise_duty_code = item_details.get('ExciseDutyCode', '')
excise_unit = item_details.get('ExciseUnit', '')
excise_rate = item_details.get('ExciseRate', '0')
excise_rule = item_details.get('ExciseRule', '2')
```

### Step 2: Extract Base Price from QuickBooks
QuickBooks selling price **includes** excise, but EFRIS expects them separate.

**Reverse Calculation:**
```python
qb_unit_price = detail.get('UnitPrice', 0)  # Includes excise

if excise_rule == "1":  # Percentage
    # QB price = base × (1 + rate/100)
    base_unit_price = qb_unit_price / (1 + rate_value / 100)
    
elif excise_rule == "2":  # Fixed-rate
    # QB price = base + rate
    base_unit_price = qb_unit_price - rate_value
```

### Step 3: Calculate Excise Tax
```python
if excise_rule == "1":  # Percentage
    excise_tax = (base_unit_price * quantity) * (rate_value / 100)
    
elif excise_rule == "2":  # Fixed-rate
    excise_tax = rate_value * quantity
```

### Step 4: Calculate VAT on (Base + Excise)
```python
net_amount = base_unit_price * quantity
taxable_amount = net_amount + excise_tax
vat_amount = taxable_amount * tax_rate  # VAT on both base and excise
```

### Step 5: Build EFRIS goodsDetails
```python
goods_item = {
    "itemCode": item_code,              # Product code
    "qty": str(quantity),
    "unitOfMeasure": excise_unit,       # MUST match T123 registration
    "unitPrice": str(base_unit_price),  # Base price (excise excluded)
    "total": str(net_amount),           # Base amount (qty × unitPrice)
    "taxRate": str(tax_rate),
    "tax": str(vat_amount),             # VAT on (base + excise)
    
    # Excise fields
    "exciseFlag": "1",                  # 1=Has excise, 2=No excise
    "categoryId": excise_duty_code,     # e.g., "LED190400"
    "exciseRate": excise_rate,          # e.g., "150"
    "exciseRule": excise_rule,          # "1" or "2"
    "exciseUnit": excise_unit,          # e.g., "102"
    "exciseCurrency": "UGX",
    "exciseTax": str(excise_tax),       # Calculated excise amount
    
    # Other fields...
}
```

---

## 4. Key Business Rules

### Price Composition
```
QuickBooks Price = Base Price + Excise Duty
EFRIS expects:
  - unitPrice = Base Price only
  - exciseTax = Separate excise amount
  - VAT = Calculated on (Base + Excise)
```

### Unit of Measure Validation
- **CRITICAL:** Invoice `unitOfMeasure` MUST match product registration (T123)
- For excisable items: Use `exciseUnit` from T125
- System auto-populates this from metadata

### Excise Rules
- **Rule 1 (Percentage):** Excise = Base × (Rate ÷ 100)
  - Example: 10% on UGX 1000 = UGX 100
- **Rule 2 (Fixed-rate):** Excise = Rate × Quantity
  - Example: UGX 150/liter × 10 liters = UGX 1500
- **Rule 3 (Combined):** Multiple rates applied
  - Treated like Rule 2 for calculations

### VAT Calculation on Excisable Items
```
Taxable Amount = Net Amount + Excise Tax
VAT = Taxable Amount × Tax Rate

Example:
  Base: UGX 1000 × 10 qty = UGX 10,000
  Excise: UGX 150/unit × 10 = UGX 1,500
  Taxable: UGX 11,500
  VAT (18%): UGX 2,070
  Total: UGX 13,570
```

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. T125 Query (Excise Duty Reference)                      │
│    → Load excise codes from database                        │
│    → Store: {code: rate, unit, currency, rule}             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Product Metadata Enrichment                             │
│    → User marks product as excisable                        │
│    → System auto-populates: ExciseRate, ExciseRule,        │
│      ExciseUnit from T125 reference                         │
│    → Store metadata in product_metadata.json               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Invoice Fetch from QuickBooks                           │
│    → Get invoice line items                                 │
│    → Enrich with product metadata (excise info)            │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Invoice Mapping (QuickBooksEfrisMapper)                 │
│    → Extract base price from QB price (reverse calc)        │
│    → Calculate excise tax based on rule                     │
│    → Calculate VAT on (base + excise)                       │
│    → Build EFRIS T109 structure with excise fields         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Submit to EFRIS (T109)                                  │
│    → Send invoice with excise data                          │
│    → EFRIS validates: excise code, rate, unit              │
│    → Returns FDN if successful                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Common Issues & Solutions

### Issue: "Unit price inconsistent with excise duty rate"
**Cause:** QB price already includes excise, but EFRIS expects base price only  
**Solution:** Reverse-calculate base price using excise rule

### Issue: "exciseUnit inconsistent with product registration"
**Cause:** Invoice unit doesn't match T123 product unit  
**Solution:** Use `excise_unit` from T125 reference for excisable items

### Issue: VAT calculated incorrectly on excisable items
**Cause:** VAT calculated on base only, not (base + excise)  
**Solution:** `taxable_amount = net_amount + excise_tax`

---

## 7. Testing Checklist

- [ ] T125 excise codes imported to database
- [ ] Products marked with correct excise duty code
- [ ] Metadata auto-populates rate, unit, rule from T125
- [ ] Invoice base price correctly extracted from QB price
- [ ] Excise tax calculated correctly (Rule 1 vs Rule 2)
- [ ] VAT calculated on (base + excise)
- [ ] Unit of measure matches product registration
- [ ] Invoice submits successfully to EFRIS
- [ ] FDN generated and stored

---

## 8. File References

- **Excise Reference Loading:** `api_multitenant.py:76-150`
- **Metadata Enrichment:** `api_multitenant.py:1181+`
- **Invoice Mapping:** `quickbooks_efris_mapper.py:180-450`
- **Database Models:** `database/models.py` (ExciseCode table)
- **Documentation:** `EXCISE_RATE_AUTO_POPULATION.md`

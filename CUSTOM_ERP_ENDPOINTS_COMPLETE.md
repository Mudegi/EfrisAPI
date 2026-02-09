# Custom ERP EFRIS Endpoints - Complete Implementation

## Strategy
**Follow QuickBooks Working Format** - All Custom ERP endpoints use the exact same EFRIS payload structure as the working QuickBooks integration.

---

## Endpoints to Implement/Align

### 1. ✅ Product Registration (T130)
**Status:** COMPLETED - Already aligned with QuickBooks

**Endpoint:** `POST /api/external/efris/register-product`

**Alignment:** Uses same `havePieceUnit="101"` format as QuickBooks

---

### 2. 🔧 Stock Increase (T131)
**Status:** NEED TO CREATE

**Endpoint:** `POST /api/external/efris/stock-increase`

**QuickBooks Reference:** Lines 4900+ in api_multitenant.py

**Implementation Plan:**
```python
@app.post("/api/external/efris/stock-increase")
async def external_stock_increase(
    stock_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Increase stock in EFRIS (T131)
    
    Request Body follows QuickBooks format:
    {
        "operation_type": "101",  # 101=Increase
        "supplier_tin": "1234567890",
        "supplier_name": "Supplier Ltd",
        "stock_in_type": "102",  # 101=Import, 102=Local Purchase, 103=Manufacture, 104=Opening Stock
        "stock_in_date": "2026-02-09",
        "items": [
            {
                "goods_code": "PROD-001",
                "quantity": 100,
                "unit_price": 5000,
                "measure_unit": "102",
                "remarks": "Stock replenishment"
            }
        ]
    }
    """
```

---

### 3. 🔧 Stock Decrease (T131)
**Status:** EXISTS - NEED TO ALIGN WITH QUICKBOOKS

**Current Endpoint:** `POST /api/external/efris/stock-decrease` (line 7877)

**Issues:**
- Uses nested `goodsStockIn` / `goodsStockInItem` structure
- Should flatten to match QuickBooks working format

**Alignment Plan:**
- Simplify request format
- Match QuickBooks T131 payload structure
- Use same field names

---

### 4. 🔧 Invoice Fiscalization (T109)
**Status:** EXISTS - NEED TO ALIGN WITH QUICKBOOKS

**Current Endpoint:** `POST /api/external/efris/submit-invoice` (line 7013)

**QuickBooks Reference:** 
- Mapper: `qb_invoice_to_efris_t109()` (line 4924)
- Working endpoint uses QuickBooksEfrisMapper

**Alignment Plan:**
- Extract QuickBooks T109 payload structure
- Apply same tax category logic (01=Standard, 02=Zero-rated, 03=Exempt)
- Use same goodsDetails format
- Match discount handling

---

### 5. 🔧 Credit Note (T110)
**Status:** EXISTS - NEED TO ALIGN WITH QUICKBOOKS

**Current Endpoint:** `POST /api/external/efris/submit-credit-note` (line 7497)

**Alignment Plan:**
- Credit notes use T109 with `invoiceType="2"`
- Match QuickBooks credit note format
- Same goodsDetails structure as invoices

---

### 6. ✅ Excise Duty Codes
**Status:** COMPLETED - Already working

**Endpoint:** `GET /api/external/efris/excise-duty` (line 7746)

**No changes needed** - fetches from database

---

### 7. ✅ Query Invoices
**Status:** COMPLETED - Already working

**Endpoints:**
- `GET /api/external/efris/invoice/{invoice_number}` (line 7687)
- `GET /api/external/efris/invoices` (line 7714)

**No changes needed** - query endpoints

---

## Implementation Priority

### Phase 1: Critical Endpoints (Stock & Invoice)
1. Create Stock Increase endpoint
2. Align Stock Decrease with QuickBooks
3. Align Invoice fiscalization with QuickBooks
4. Align Credit Note with QuickBooks

### Phase 2: Testing
1. Test product registration (already working)
2. Test stock increase/decrease
3. Test invoice fiscalization
4. Test credit notes

---

## Next Steps

I'll now implement all the alignments. Should I:

**Option A:** Update all endpoints in one commit (cleaner)
**Option B:** Update one endpoint at a time with testing between each

Which approach do you prefer?

"""
Multi-Tenant EFRIS API - Production Ready
FastAPI application with database, authentication, and company isolation
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from database.connection import get_db, init_db
from database.models import (
    User, Company, CompanyUser, Product, Invoice, PurchaseOrder, CreditMemo,
    EFRISGood, EFRISInvoice, ExciseCode
)
from auth.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, verify_company_access, get_user_companies
)
from schemas.schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    CompanyCreate, CompanyResponse, CompanyWithRole, CompanyUserAdd,
    ProductResponse, InvoiceResponse
)
from efris_client import EfrisManager
from quickbooks_client import QuickBooksClient
from quickbooks_efris_mapper import QuickBooksEfrisMapper

load_dotenv()

app = FastAPI(
    title=os.getenv("API_TITLE", "EFRIS Multi-Tenant API"),
    version=os.getenv("API_VERSION", "2.0.0"),
    description="Production-ready multi-tenant EFRIS integration with PostgreSQL"
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# ========== GLOBAL MANAGERS AND HELPERS ==========

# Company-specific EFRIS managers cache
efris_managers: Dict[int, EfrisManager] = {}

# Initialize QuickBooks client (shared across companies for now)
qb_client = QuickBooksClient(
    client_id=os.getenv('QB_CLIENT_ID', 'your_client_id'),
    client_secret=os.getenv('QB_CLIENT_SECRET', 'your_client_secret'),
    redirect_uri=os.getenv('QB_REDIRECT_URI', 'http://localhost:8001/api/quickbooks/callback'),
    environment=os.getenv('QB_ENVIRONMENT', 'sandbox')
)

# Try to load existing tokens
try:
    qb_client.load_tokens()
except Exception as e:
    print(f"[QB] Could not load tokens: {e}")

# Product metadata cache (stores excise info for products)
PRODUCT_METADATA_FILE = 'product_metadata.json'
product_metadata = {}

# Excise duty reference data (will be loaded from database)
excise_duty_reference = {}


def get_efris_manager(company: Company) -> EfrisManager:
    """Get or create EFRIS manager for a company"""
    if company.id not in efris_managers:
        efris_managers[company.id] = EfrisManager(
            tin=company.tin,
            test_mode=True  # TODO: Make this configurable per company
        )
    return efris_managers[company.id]


def load_excise_duty_reference_from_db(company_id: int, db: Session):
    """Load excise duty reference from database for a company"""
    try:
        # Query all excise codes for this company
        codes = db.query(ExciseCode).filter(ExciseCode.company_id == company_id).all()
        
        if not codes:
            return {}
        
        # Build reference dict
        ref_dict = {}
        for code in codes:
            ref_dict[code.excise_code] = {
                'rate': code.excise_rate or '',
                'unit': code.excise_unit or '',
                'currency': code.excise_currency or '',
                'exciseRule': code.excise_rule or '1',
                'goodService': code.excise_name or '',
                'rateText': code.rate_text or ''
            }
        
        return ref_dict
        
    except Exception as e:
        print(f"[EXCISE REF] Error loading from database: {e}")
        return {}


def get_excise_rate(excise_code: str, company_id: int, db: Session) -> str:
    """Get the excise rate for a given excise duty code"""
    excise_ref = load_excise_duty_reference_from_db(company_id, db)
    if excise_code in excise_ref:
        return excise_ref[excise_code].get('rate', '0')
    return '0'


def get_excise_rule(excise_code: str, company_id: int, db: Session) -> str:
    """Get the excise rule for a given excise duty code
    Returns: '1' for percentage-based, '2' for fixed-rate
    """
    excise_ref = load_excise_duty_reference_from_db(company_id, db)
    if excise_code in excise_ref:
        return excise_ref[excise_code].get('exciseRule', '2')
    return '2'


def get_excise_unit(excise_code: str, company_id: int, db: Session) -> str:
    """Get the unit of measurement for a given excise duty code
    Returns: unit code (e.g., '101' for pieces, '102' for liters, '104' for kg)
    """
    excise_ref = load_excise_duty_reference_from_db(company_id, db)
    if excise_code in excise_ref:
        ref_data = excise_ref[excise_code]
        unit = ref_data.get('unit', '')
        if unit:  # Return the unit if it exists
            return unit
        return '101'  # Default to pieces if no unit specified
    return '101'  # Default to pieces


def load_product_metadata():
    """Load product metadata from file"""
    global product_metadata
    if os.path.exists(PRODUCT_METADATA_FILE):
        try:
            with open(PRODUCT_METADATA_FILE, 'r') as f:
                product_metadata = json.load(f)
        except Exception as e:
            print(f"[Metadata] Error loading product metadata: {e}")
            product_metadata = {}
    else:
        product_metadata = {}


def save_product_metadata(metadata=None):
    """Save product metadata to file"""
    try:
        data_to_save = metadata if metadata is not None else product_metadata
        with open(PRODUCT_METADATA_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"[Metadata] Error saving product metadata: {e}")


# ========== STARTUP ==========

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    load_product_metadata()
    print("[OK] Database tables created")
    print("[OK] Multi-tenant EFRIS API started")


# ========== ROOT & DASHBOARD ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to dashboard"""
    return FileResponse("static/dashboard_multitenant.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the multi-tenant dashboard"""
    return FileResponse("static/dashboard_multitenant.html")


# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


# ========== COMPANY ENDPOINTS ==========

@app.get("/api/companies", response_model=List[CompanyWithRole])
async def get_my_companies(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all companies user has access to"""
    company_users = db.query(CompanyUser).filter(CompanyUser.user_id == current_user.id).all()
    
    result = []
    for cu in company_users:
        company_dict = {
            "id": cu.company.id,
            "name": cu.company.name,
            "tin": cu.company.tin,
            "device_no": cu.company.device_no,
            "efris_test_mode": cu.company.efris_test_mode,
            "qb_company_name": cu.company.qb_company_name,
            "is_active": cu.company.is_active,
            "created_at": cu.company.created_at,
            "role": cu.role
        }
        result.append(company_dict)
    
    return result


@app.post("/api/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new company and assign current user as admin"""
    # Check if TIN exists
    existing = db.query(Company).filter(Company.tin == company_data.tin).first()
    if existing:
        raise HTTPException(status_code=400, detail="TIN already registered")
    
    # Create company
    db_company = Company(
        name=company_data.name,
        tin=company_data.tin,
        device_no=company_data.device_no,
        efris_test_mode=company_data.efris_test_mode
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    # Add current user as admin
    company_user = CompanyUser(
        user_id=current_user.id,
        company_id=db_company.id,
        role="admin"
    )
    db.add(company_user)
    db.commit()
    
    return db_company


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get company details"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@app.post("/api/companies/{company_id}/users")
async def add_company_user(
    company_id: int,
    user_data: CompanyUserAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add user to company (admin only)"""
    from auth.security import verify_company_admin
    
    if not verify_company_admin(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already added
    existing = db.query(CompanyUser).filter(
        CompanyUser.user_id == user.id,
        CompanyUser.company_id == company_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has access")
    
    # Add user to company
    company_user = CompanyUser(
        user_id=user.id,
        company_id=company_id,
        role=user_data.role
    )
    db.add(company_user)
    db.commit()
    
    return {"message": "User added successfully"}


# ========== PRODUCT ENDPOINTS ==========

@app.get("/api/companies/{company_id}/products", response_model=List[ProductResponse])
async def get_company_products(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all products for a company with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(Product).filter(Product.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.qb_name.ilike(search_pattern)) |
            (Product.qb_sku.ilike(search_pattern)) |
            (Product.qb_description.ilike(search_pattern))
        )
    
    products = query.order_by(Product.updated_at.desc()).all()
    return products


# ========== INVOICE ENDPOINTS ==========

@app.get("/api/companies/{company_id}/invoices", response_model=List[InvoiceResponse])
async def get_company_invoices(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all invoices for a company with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(Invoice).filter(Invoice.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Invoice.qb_doc_number.ilike(search_pattern)) |
            (Invoice.qb_customer_name.ilike(search_pattern))
        )
    
    invoices = query.order_by(Invoice.qb_txn_date.desc()).all()
    return invoices


# ========== EFRIS ENDPOINTS ==========

@app.post("/api/test/t104-key-exchange")
async def test_t104_key_exchange():
    """Test endpoint for T104 - Obtaining Symmetric Key and Signature"""
    try:
        test_manager = EfrisManager(tin='1014409555', test_mode=True)
        t104_payload = test_manager._build_handshake_payload("T104", "")
        
        response = test_manager.session.post(
            test_manager.base_url,
            json=t104_payload,
            headers=test_manager._get_headers()
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return_code = response_data.get('returnStateInfo', {}).get('returnCode')
            
            if return_code == "00":
                return {
                    "status": "SUCCESS",
                    "message": "T104 Key Exchange Successful",
                    "full_response": response_data
                }
            else:
                return {
                    "status": "FAILED",
                    "full_response": response_data
                }
        else:
            return {
                "status": "HTTP_ERROR",
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/registration-details")
async def get_registration_details(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get company registration details from EFRIS"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        details = manager.get_registration_details()
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/code-list")
async def get_code_list(
    company_id: int,
    code_type: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T106 - Query code lists from EFRIS (units, currencies, commodity categories)"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.get_code_list(code_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/goods-and-services")
async def get_goods_and_services(
    company_id: int,
    page_no: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    goods_code: str = Query(None),
    goods_name: str = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T127 - Goods/Services Inquiry"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.get_goods_and_services(
            page_no=page_no,
            page_size=page_size,
            goods_code=goods_code,
            goods_name=goods_name
        )
        
        if isinstance(result, dict) and 'data' in result:
            if 'decrypted_content' in result['data']:
                return result['data']['decrypted_content']
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/efris-goods/import")
async def import_efris_goods(
    company_id: int,
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Import goods from EFRIS and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.get_goods_and_services(page_no=1, page_size=page_size)
        
        if isinstance(result, dict) and 'data' in result and 'decrypted_content' in result['data']:
            data = result['data']['decrypted_content']
            records = data.get('records', [])
            
            # Save to database
            saved_count = 0
            for record in records:
                # Check if already exists
                existing = db.query(EFRISGood).filter(
                    EFRISGood.company_id == company_id,
                    EFRISGood.goods_code == record.get('goodsCode')
                ).first()
                
                if existing:
                    # Update existing
                    existing.goods_name = record.get('goodsName')
                    existing.commodity_category_code = record.get('commodityCategoryCode')
                    existing.commodity_category_name = record.get('commodityCategoryName')
                    existing.unit_price = float(record.get('unitPrice', 0))
                    existing.currency = record.get('currency')
                    existing.tax_rate = float(record.get('taxRate', 0))
                    existing.have_excise_tax = record.get('haveExciseTax')
                    existing.stock = float(record.get('stock', 0))
                    existing.efris_data = record
                    existing.updated_at = datetime.now()
                else:
                    # Create new
                    good = EFRISGood(
                        company_id=company_id,
                        goods_code=record.get('goodsCode'),
                        goods_name=record.get('goodsName'),
                        commodity_category_code=record.get('commodityCategoryCode'),
                        commodity_category_name=record.get('commodityCategoryName'),
                        unit_price=float(record.get('unitPrice', 0)),
                        currency=record.get('currency'),
                        tax_rate=float(record.get('taxRate', 0)),
                        have_excise_tax=record.get('haveExciseTax'),
                        stock=float(record.get('stock', 0)),
                        efris_data=record
                    )
                    db.add(good)
                saved_count += 1
            
            db.commit()
            return {"message": f"Imported {saved_count} goods from EFRIS", "records": records}
        
        return {"message": "No data received from EFRIS", "records": []}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/efris-goods")
async def get_efris_goods(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get EFRIS goods from database with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(EFRISGood).filter(EFRISGood.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (EFRISGood.goods_code.ilike(search_pattern)) |
            (EFRISGood.goods_name.ilike(search_pattern))
        )
    
    goods = query.order_by(EFRISGood.updated_at.desc()).all()
    
    return [
        {
            "id": g.id,
            "goodsCode": g.goods_code,
            "goodsName": g.goods_name,
            "commodityCategoryCode": g.commodity_category_code,
            "commodityCategoryName": g.commodity_category_name,
            "unitPrice": g.unit_price,
            "currency": g.currency,
            "taxRate": g.tax_rate,
            "haveExciseTax": g.have_excise_tax,
            "stock": g.stock,
            "importedAt": g.imported_at.isoformat() if g.imported_at else None
        }
        for g in goods
    ]


@app.post("/api/companies/{company_id}/goods-upload")
async def upload_goods(
    company_id: int,
    products: List[dict] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T130 - Goods Upload (Register/Update Products)"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.upload_goods(products)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/stock-increase")
async def stock_increase(
    company_id: int,
    stock_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T131 - Stock Increase"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.stock_increase(stock_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/stock-decrease")
async def stock_decrease(
    company_id: int,
    stock_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T132 - Stock Decrease"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.stock_decrease(stock_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/upload-invoice")
async def upload_invoice(
    company_id: int,
    invoice_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T109 - Upload and Fiscalize Invoice"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.upload_invoice(invoice_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/credit-note")
async def create_credit_note(
    company_id: int,
    credit_note_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T110 - Credit Note"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.create_credit_note(credit_note_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/query-invoices")
async def query_invoices(
    company_id: int,
    query_params: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T111 - Query Invoices"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.query_invoices(query_params)
        
        # Extract decrypted content if available
        if isinstance(result, dict) and 'data' in result:
            if 'decrypted_content' in result['data']:
                return result['data']['decrypted_content']
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/efris-invoices/import")
async def import_efris_invoices(
    company_id: int,
    query_params: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Import invoices from EFRIS and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.query_invoices(query_params)
        
        if isinstance(result, dict) and 'data' in result and 'decrypted_content' in result['data']:
            data = result['data']['decrypted_content']
            records = data.get('records', [])
            
            # Save to database
            saved_count = 0
            for record in records:
                # Check if already exists
                existing = db.query(EFRISInvoice).filter(
                    EFRISInvoice.company_id == company_id,
                    EFRISInvoice.invoice_no == record.get('invoiceNo')
                ).first()
                
                # Parse issued date
                issued_date = None
                try:
                    if record.get('issuedDate'):
                        issued_date = datetime.strptime(record.get('issuedDate'), '%d/%m/%Y %H:%M:%S')
                except:
                    pass
                
                if existing:
                    # Update existing
                    existing.invoice_kind = record.get('invoiceKind')
                    existing.invoice_type = record.get('invoiceType')
                    existing.invoice_industry_code = record.get('invoiceIndustryCode')
                    existing.buyer_legal_name = record.get('buyerLegalName')
                    existing.buyer_business_name = record.get('buyerBusinessName')
                    existing.buyer_tin = record.get('buyerTin')
                    existing.currency = record.get('currency')
                    existing.gross_amount = float(record.get('grossAmount', 0))
                    existing.tax_amount = float(record.get('taxAmount', 0))
                    existing.net_amount = float(record.get('netAmount', 0)) if record.get('netAmount') else None
                    existing.issued_date_str = record.get('issuedDateStr')
                    existing.issued_date = issued_date
                    existing.uploading_time = record.get('uploadingTime')
                    existing.is_invalid = record.get('isInvalid')
                    existing.is_refund = record.get('isRefund')
                    existing.reference_no = record.get('referenceNo')
                    existing.device_no = record.get('deviceNo')
                    existing.efris_data = record
                    existing.updated_at = datetime.now()
                else:
                    # Create new
                    invoice = EFRISInvoice(
                        company_id=company_id,
                        invoice_no=record.get('invoiceNo'),
                        invoice_kind=record.get('invoiceKind'),
                        invoice_type=record.get('invoiceType'),
                        invoice_industry_code=record.get('invoiceIndustryCode'),
                        buyer_legal_name=record.get('buyerLegalName'),
                        buyer_business_name=record.get('buyerBusinessName'),
                        buyer_tin=record.get('buyerTin'),
                        currency=record.get('currency'),
                        gross_amount=float(record.get('grossAmount', 0)),
                        tax_amount=float(record.get('taxAmount', 0)),
                        net_amount=float(record.get('netAmount', 0)) if record.get('netAmount') else None,
                        issued_date_str=record.get('issuedDateStr'),
                        issued_date=issued_date,
                        uploading_time=record.get('uploadingTime'),
                        is_invalid=record.get('isInvalid'),
                        is_refund=record.get('isRefund'),
                        reference_no=record.get('referenceNo'),
                        device_no=record.get('deviceNo'),
                        efris_data=record
                    )
                    db.add(invoice)
                saved_count += 1
            
            db.commit()
            
            # Update any QB invoices that match EFRIS invoices
            updated_count = 0
            for record in records:
                fdn = record.get('invoiceNo')
                reference_no = record.get('referenceNo')  # This should be the QB DocNumber
                
                if fdn:
                    # Try to find QB invoice by reference number first (most reliable)
                    qb_invoice = None
                    if reference_no:
                        qb_invoice = db.query(EFRISInvoice).filter(
                            EFRISInvoice.company_id == company_id,
                            EFRISInvoice.qb_invoice_number == reference_no,
                            EFRISInvoice.fdn.is_(None)
                        ).first()
                    
                    # If not found, try by error message containing the FDN
                    if not qb_invoice:
                        qb_invoice = db.query(EFRISInvoice).filter(
                            EFRISInvoice.company_id == company_id,
                            EFRISInvoice.fdn.is_(None),
                            EFRISInvoice.status == 'failed'
                        ).filter(
                            EFRISInvoice.error_message.ilike(f'%{fdn}%')
                        ).first()
                    
                    if qb_invoice:
                        qb_invoice.status = 'success'
                        qb_invoice.fdn = fdn
                        qb_invoice.invoice_no = fdn
                        qb_invoice.error_message = None
                        updated_count += 1
            
            if updated_count > 0:
                db.commit()
            
            return {
                "message": f"Imported {saved_count} invoices from EFRIS, updated {updated_count} QB invoice statuses",
                "records": records
            }
        
        return {"message": "No data received from EFRIS", "records": []}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/efris-invoices")
async def get_efris_invoices(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get EFRIS invoices from database with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(EFRISInvoice).filter(EFRISInvoice.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (EFRISInvoice.invoice_no.ilike(search_pattern)) |
            (EFRISInvoice.buyer_legal_name.ilike(search_pattern)) |
            (EFRISInvoice.buyer_business_name.ilike(search_pattern))
        )
    
    invoices = query.order_by(EFRISInvoice.issued_date.desc()).all()
    
    return [
        {
            "id": inv.id,
            "invoiceNo": inv.invoice_no,
            "invoiceKind": inv.invoice_kind,
            "buyerLegalName": inv.buyer_legal_name,
            "buyerBusinessName": inv.buyer_business_name,
            "currency": inv.currency,
            "grossAmount": str(inv.gross_amount) if inv.gross_amount else "0",
            "taxAmount": str(inv.tax_amount) if inv.tax_amount else "0",
            "issuedDateStr": inv.issued_date_str,
            "referenceNo": inv.reference_no,
            "isInvalid": inv.is_invalid,
            "isRefund": inv.is_refund,
            "importedAt": inv.imported_at.isoformat() if inv.imported_at else None
        }
        for inv in invoices
    ]


@app.get("/api/companies/{company_id}/invoice/{invoice_no}")
async def get_invoice(
    company_id: int,
    invoice_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific invoice details"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.get_invoice(invoice_no)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/excise-duty")
async def get_excise_duty(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T125 - Query Excise Duty and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.query_excise_duty()
        
        # Extract excise list from response
        excise_list = result.get('data', {}).get('decrypted_content', {}).get('exciseDutyList', [])
        
        if excise_list:
            # Clear existing codes for this company
            db.query(ExciseCode).filter(ExciseCode.company_id == company_id).delete()
            
            # Save new codes to database
            codes_saved = 0
            for duty in excise_list:
                code = duty.get('exciseDutyCode')
                if not code or duty.get('isLeafNode') != '1':
                    continue  # Only save leaf nodes
                
                details_list = duty.get('exciseDutyDetailsList', [])
                if not details_list:
                    continue
                
                # Check for type 102 (fixed rate) or type 101 (percentage)
                type_102_detail = next((d for d in details_list if d.get('type') == '102'), None)
                type_101_detail = next((d for d in details_list if d.get('type') == '101'), None)
                
                rate = ''
                unit = ''
                currency = '101'
                excise_rule = '1'
                rate_text = ''
                
                if type_102_detail:
                    rate = type_102_detail.get('rate', '0')
                    unit = type_102_detail.get('unit', '')
                    currency = type_102_detail.get('currency', '101')
                    excise_rule = '2'
                elif type_101_detail:
                    rate = type_101_detail.get('rate', '0')
                    excise_rule = '1'
                
                # Build rate text
                for detail in details_list:
                    detail_type = detail.get('type')
                    if detail_type == '101':
                        pct = detail.get('rate', '')
                        rate_text = f"{pct}%" if rate_text == '' else f"{rate_text},{pct}%"
                    elif detail_type == '102':
                        amt = detail.get('rate', '')
                        u = detail.get('unit', '')
                        c = detail.get('currency', '')
                        unit_name = {
                            '101': 'Piece', '102': 'Litre', '103': 'Box', 
                            '104': 'Kilogram', '105': 'Meter'
                        }.get(u, 'Unit')
                        curr_name = 'UGX' if c == '101' else c
                        rate_text = f"{rate_text},{curr_name}{amt} per {unit_name}" if rate_text else f"{curr_name}{amt} per {unit_name}"
                
                # Create excise code record
                excise_code = ExciseCode(
                    company_id=company_id,
                    excise_code=code,
                    excise_name=duty.get('goodService', ''),
                    excise_rate=rate,
                    excise_unit=unit,
                    excise_currency=currency,
                    excise_rule=excise_rule,
                    rate_text=rate_text,
                    is_leaf_node=True
                )
                db.add(excise_code)
                codes_saved += 1
            
            db.commit()
            print(f"[EXCISE DB] Saved {codes_saved} excise codes for company {company_id}")
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/excise-codes")
async def get_excise_codes_from_db(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get excise codes from database for a company"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        codes = db.query(ExciseCode).filter(ExciseCode.company_id == company_id).all()
        
        # Format as list for frontend
        result = []
        for code in codes:
            result.append({
                'exciseDutyCode': code.excise_code,
                'goodService': code.excise_name,
                'rate': code.excise_rate,
                'unit': code.excise_unit,
                'currency': code.excise_currency,
                'exciseRule': code.excise_rule,
                'rateText': code.rate_text,
                'isLeafNode': '1'
            })
        
        return {
            'success': True,
            'count': len(result),
            'codes': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/query-credit-notes")
async def query_credit_notes(
    company_id: int,
    query_params: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """T112 - Query Credit Notes"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.query_credit_notes(query_params)
        
        # Extract decrypted content if available
        if isinstance(result, dict) and 'data' in result:
            if 'decrypted_content' in result['data']:
                return result['data']['decrypted_content']
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/generate-fiscal-invoice")
async def generate_fiscal_invoice(
    company_id: int,
    invoice_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate fiscal invoice"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        invoice = manager.generate_invoice(invoice_data)
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": invoice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/generate-fiscal-receipt")
async def generate_fiscal_receipt(
    company_id: int,
    receipt_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate fiscal receipt"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        receipt = manager.generate_invoice(receipt_data)  # Or add separate method
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": receipt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/query-taxpayer/{tin}")
async def query_taxpayer(
    company_id: int,
    tin: str,
    ninBrn: str = Query(default=""),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Query taxpayer information by TIN"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.query_taxpayer_by_tin(tin, ninBrn)
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/get-server-time")
async def get_server_time_api(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get EFRIS server time"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        result = manager.get_server_time()
        return {
            "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== QUICKBOOKS INTEGRATION ==========

@app.get("/api/quickbooks/status")
async def quickbooks_status():
    """Check QuickBooks connection status"""
    try:
        if not qb_client.access_token:
            return {"connected": False, "message": "Not connected to QuickBooks", "access_token": False}
        
        # Try to actually call QuickBooks API to verify token works
        try:
            company_info = qb_client.get_company_info()
            
            return {
                "connected": True,
                "access_token": True,
                "companyName": company_info.get('CompanyName'),
                "realmId": qb_client.realm_id,
                "tokenExpiry": qb_client.token_expiry.isoformat() if qb_client.token_expiry else None
            }
        except Exception as api_error:
            # Token exists but doesn't work - needs refresh or reconnect
            return {
                "connected": False, 
                "access_token": False,
                "message": "QuickBooks token expired or invalid",
                "error": str(api_error)
            }
    except Exception as e:
        return {"connected": False, "access_token": False, "error": str(e)}


@app.get("/api/quickbooks/auth")
async def quickbooks_auth():
    """Initiate QuickBooks OAuth flow"""
    try:
        auth_url = qb_client.get_authorization_url()
        return {"authUrl": auth_url, "message": "Visit this URL to authorize QuickBooks access"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/refresh")
async def refresh_quickbooks_token():
    """Manually refresh QuickBooks access token"""
    try:
        if not qb_client.refresh_token:
            raise HTTPException(status_code=400, detail="No refresh token available. Please reconnect QuickBooks.")
        
        result = qb_client.refresh_access_token()
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "tokenExpiry": qb_client.token_expiry.isoformat() if qb_client.token_expiry else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(
    code: Optional[str] = None, 
    realmId: Optional[str] = None, 
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle QuickBooks OAuth callback"""
    if error:
        error_msg = error_description or error
        return RedirectResponse(url=f"/?error={error_msg}")
    
    if not code or not realmId:
        return RedirectResponse(url="/?error=Missing authorization code or realm ID")
    
    try:
        tokens = qb_client.exchange_code_for_tokens(code)
        qb_client.realm_id = realmId
        
        # Detect QB region from company info
        qb_region = qb_client.detect_region()
        company_info = qb_client.get_company_info()
        
        # Check if this is a new sandbox connection
        if state and state.startswith("new_sandbox_"):
            company_id = int(state.split("_")[-1])
            
            # Store QB connection details in database for this specific company
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.qb_realm_id = realmId
                company.qb_access_token = qb_client.access_token
                company.qb_refresh_token = qb_client.refresh_token
                company.qb_token_expires = qb_client.token_expiry
                company.qb_company_name = company_info.get('CompanyName', 'Unknown')
                company.qb_region = qb_region
                db.commit()
                
                print(f"[QB] NEW SANDBOX Connected for company {company.name}: {company_info.get('CompanyName', 'Unknown')} (Region: {qb_region})")
                return RedirectResponse(url="/?connected=true&type=new_sandbox")
        
        # Regular connection flow - save to global tokens file
        qb_client.save_tokens()
        
        print(f"[QB] Connected to {company_info.get('CompanyName', 'Unknown')} (Region: {qb_region})")
        
        return RedirectResponse(url="/?connected=true")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")


@app.post("/api/companies/{company_id}/quickbooks/disconnect")
async def disconnect_quickbooks(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect QuickBooks from this company"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Clear QuickBooks connection for this company
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Clear QB fields
        company.qb_realm_id = None
        company.qb_access_token = None
        company.qb_refresh_token = None
        company.qb_token_expires = None
        company.qb_company_name = None
        company.qb_region = None
        
        db.commit()
        
        # Clear global QB client (TODO: make this per-company)
        qb_client.access_token = None
        qb_client.refresh_token = None
        qb_client.realm_id = None
        qb_client.token_expiry = None
        
        return {"message": "QuickBooks disconnected successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@app.post("/api/companies/{company_id}/quickbooks/connect")
async def connect_quickbooks(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initiate QuickBooks OAuth for a specific company"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Store company_id in session/state for OAuth callback
        auth_url = qb_client.get_authorization_url(state=str(company_id))
        return {"authorization_url": auth_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate connection: {str(e)}")


@app.post("/api/companies/{company_id}/quickbooks/connect-new-sandbox")
async def connect_new_quickbooks_sandbox(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Connect to a different QuickBooks sandbox - starts a new OAuth flow"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Create a new QB client instance for this authorization
        new_qb_client = QuickBooksClient(
            client_id=os.getenv('QB_CLIENT_ID'),
            client_secret=os.getenv('QB_CLIENT_SECRET'),
            redirect_uri=os.getenv('QB_REDIRECT_URI', 'http://localhost:8001/api/quickbooks/callback'),
            environment="sandbox"
        )
        
        # Clear existing QuickBooks connection data for this company
        company.qb_realm_id = None
        company.qb_access_token = None
        company.qb_refresh_token = None
        company.qb_token_expires = None
        company.qb_company_name = None
        company.qb_region = None
        db.commit()
        
        # Also clear the global client (will be replaced after new authorization)
        qb_client.access_token = None
        qb_client.refresh_token = None
        qb_client.realm_id = None
        qb_client.token_expiry = None
        
        # Generate authorization URL with company_id in state
        auth_url = new_qb_client.get_authorization_url(state=f"new_sandbox_{company_id}")
        
        return {
            "authorization_url": auth_url,
            "message": "Visit this URL to authorize access to a different QuickBooks sandbox",
            "action": "new_sandbox_connection"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to initiate new sandbox connection: {str(e)}")


@app.get("/api/quickbooks/items")
async def get_quickbooks_items(
    company_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch all items from QuickBooks with EFRIS registration status"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        # Check QB connection first
        if not qb_client.access_token:
            raise HTTPException(status_code=400, detail="QuickBooks not connected. Please connect first.")
        
        print(f"[QB] Fetching items for company {company_id}")
        # Fetch QuickBooks items
        items = qb_client.get_all_items()
        print(f"[QB] Fetched {len(items)} items")
        
        # Enrich with full details
        for item in items:
            item_id = item.get('Id')
            if item_id:
                full_item = qb_client.get_item_by_id(item_id)
                if full_item:
                    item.update(full_item)
        
        # Fetch EFRIS products for comparison
        efris_products = []
        page = 1
        while True:
            result = manager.get_goods_and_services(page_no=page, page_size=10)
            if result.get('returnStateInfo', {}).get('returnCode') == '00':
                goods_list = result.get('data', {}).get('goodsInfoList', [])
                if not goods_list:
                    break
                efris_products.extend(goods_list)
                page += 1
                if len(goods_list) < 10:
                    break
            else:
                break
        
        # Create lookup map
        efris_lookup = {p.get('goodsCode'): p for p in efris_products}
        
        # Add registration status
        for item in items:
            product_code = item.get('Description') or item.get('Name', '')
            if product_code in efris_lookup:
                item['EfrisStatus'] = 'Registered'
                item['EfrisId'] = efris_lookup[product_code].get('id')
            else:
                item['EfrisStatus'] = 'Pending Registration'
        
        return {
            "count": len(items),
            "registered": len([i for i in items if i.get('EfrisStatus') == 'Registered']),
            "pending": len([i for i in items if i.get('EfrisStatus') == 'Pending Registration']),
            "items": items
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[QB] Error fetching items: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"QuickBooks fetch failed: {str(e)}")


@app.post("/api/quickbooks/sync-products")
async def sync_products_to_efris(
    company_id: int = Query(...),
    payload: dict = Body(...),
    default_category_id: str = Query("50202306"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync selected products from QuickBooks to EFRIS"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        qb_items = payload.get('products', [])
        if not qb_items:
            raise HTTPException(status_code=400, detail="No products provided")
        
        efris_products = []
        for item in qb_items:
            operation_type = "102" if item.get('EfrisStatus') == 'Registered' else "101"
            cost_price = item.get('PurchaseCost') or item.get('UnitPrice', 0)
            is_service = item.get('Type') == 'Service'
            goods_code = item.get('Description', '') or item.get('Name', '')
            measure_unit = '102' if is_service else item.get('UnitOfMeasure', '101')
            
            efris_product = {
                "operationType": operation_type,
                "goodsName": item.get('Name', ''),
                "goodsCode": goods_code,
                "measureUnit": measure_unit,
                "unitPrice": str(cost_price),
                "currency": "101",
                "commodityCategoryId": item.get('Sku', default_category_id),
                "haveExciseTax": "101" if item.get('HasExcise') else "102",
                "goodsTypeCode": "102" if is_service else "101",
                "description": goods_code,
                "havePieceUnit": "101",
                "pieceMeasureUnit": measure_unit,
                "pieceUnitPrice": str(cost_price),
                "packageScaledValue": "1",
                "pieceScaledValue": "1"
            }
            
            if is_service:
                efris_product["stockPrewarning"] = "0"
                efris_product["stockPrequantity"] = "0"
            else:
                efris_product["stockPrewarning"] = "10"
                efris_product["stockPrequantity"] = str(item.get('QtyOnHand', 0))
            
            if item.get('HasExcise'):
                efris_product["exciseDutyCode"] = item.get('ExciseDutyCode', 'LED050000')
            
            if operation_type == "102" and item.get('EfrisId'):
                efris_product["id"] = item.get('EfrisId')
            
            efris_products.append(efris_product)
        
        result = manager.upload_goods(efris_products)
        
        return {
            "synced_count": len(efris_products),
            "message": f"Synced {len(efris_products)} products to EFRIS",
            "efrisResponse": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/efris-invoice/{qb_invoice_id}")
async def get_efris_invoice_details(
    company_id: int,
    qb_invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored EFRIS invoice details for a QuickBooks invoice"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    efris_inv = db.query(EFRISInvoice).filter(
        EFRISInvoice.company_id == company_id,
        EFRISInvoice.qb_invoice_id == qb_invoice_id
    ).first()
    
    if not efris_inv:
        raise HTTPException(status_code=404, detail="EFRIS invoice not found")
    
    # Extract decrypted content from response
    efris_invoice = None
    antifake_code = None
    
    if efris_inv.efris_response:
        decrypted = efris_inv.efris_response.get('data', {}).get('decrypted_content', {})
        if decrypted:
            # Check if we have full invoice details or just existInvoiceList
            if 'basicInformation' in decrypted:
                # Full invoice details available
                efris_invoice = decrypted
                antifake_code = decrypted.get('basicInformation', {}).get('antifakeCode', '')
            elif 'existInvoiceList' in decrypted and efris_inv.fdn:
                # Only have FDN from duplicate response, use efris_data if available
                if efris_inv.efris_data:
                    # Build invoice details from stored EFRIS data
                    efris_invoice = {
                        'basicInformation': {
                            'invoiceNo': efris_inv.fdn,
                            'currency': efris_inv.currency or 'UGX',
                            'antifakeCode': decrypted.get('existInvoiceList', [{}])[0].get('antiFakeCode', '') if decrypted.get('existInvoiceList') else ''
                        },
                        'buyerDetails': {
                            'buyerLegalName': efris_inv.buyer_legal_name,
                            'buyerBusinessName': efris_inv.buyer_business_name,
                            'buyerTin': efris_inv.buyer_tin
                        },
                        'summary': {
                            'grossAmount': str(efris_inv.gross_amount) if efris_inv.gross_amount else '0',
                            'netAmount': str(efris_inv.net_amount) if efris_inv.net_amount else '0'
                        },
                        'taxDetails': {
                            'taxAmount': str(efris_inv.tax_amount) if efris_inv.tax_amount else '0'
                        }
                    }
                    antifake_code = efris_invoice['basicInformation']['antifakeCode']
    
    return {
        "qb_invoice_id": qb_invoice_id,
        "qb_invoice_number": efris_inv.qb_invoice_number,
        "fdn": efris_inv.fdn,
        "efris_invoice_id": efris_inv.efris_invoice_id,
        "status": efris_inv.status,
        "antifake_code": antifake_code,
        "efris_invoice": efris_invoice,
        "created_at": str(efris_inv.created_at) if efris_inv.created_at else None
    }


@app.get("/api/quickbooks/invoices")
async def get_quickbooks_invoices(
    company_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch invoices from QuickBooks with EFRIS status"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # First, auto-fix any successful invoices with missing FDN
        fix_missing_fdns(db, company_id)
        
        invoices = qb_client.get_invoices(start_date=start_date, end_date=end_date)
        
        # Enrich with EFRIS status and FDN
        for invoice in invoices:
            invoice_id = invoice.get('Id')
            efris_inv = db.query(EFRISInvoice).filter(
                EFRISInvoice.company_id == company_id,
                EFRISInvoice.qb_invoice_id == invoice_id
            ).first()
            
            if efris_inv:
                invoice['EfrisStatus'] = efris_inv.status
                invoice['EfrisFDN'] = efris_inv.fdn
                invoice['EfrisInvoiceId'] = efris_inv.efris_invoice_id
            else:
                invoice['EfrisStatus'] = 'draft'
                invoice['EfrisFDN'] = None
                invoice['EfrisInvoiceId'] = None
        
        # Sort by TxnDate descending (most recent first)
        invoices.sort(key=lambda x: x.get('TxnDate', ''), reverse=True)
        
        return {
            "count": len(invoices),
            "invoices": invoices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def fix_missing_fdns(db: Session, company_id: int):
    """Auto-fix successful invoices that have missing FDN by extracting from stored response"""
    try:
        invoices = db.query(EFRISInvoice).filter(
            EFRISInvoice.company_id == company_id,
            EFRISInvoice.status == 'success',
            (EFRISInvoice.fdn == None) | (EFRISInvoice.fdn == '')
        ).all()
        
        fixed = 0
        for inv in invoices:
            if inv.efris_response:
                decrypted = inv.efris_response.get('data', {}).get('decrypted_content', {})
                basic_info = decrypted.get('basicInformation', {})
                fdn = basic_info.get('invoiceNo', '')
                invoice_id = basic_info.get('invoiceId', '')
                
                if fdn:
                    inv.fdn = fdn
                    inv.efris_invoice_id = invoice_id
                    fixed += 1
                    print(f"[FIX] Updated FDN for QB Invoice {inv.qb_invoice_number}: {fdn}")
        
        if fixed > 0:
            db.commit()
            print(f"[FIX] Auto-fixed {fixed} invoices with missing FDN")
    except Exception as e:
        print(f"[FIX] Error fixing FDNs: {e}")


@app.post("/api/quickbooks/sync-invoice/{invoice_id}")
async def sync_invoice_to_efris(
    invoice_id: str,
    company_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync specific invoice from QuickBooks to EFRIS"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        qb_invoice = qb_client.get_invoice_by_id(invoice_id)
        customer_ref = qb_invoice.get('CustomerRef', {})
        qb_customer = qb_client.get_customer_by_id(customer_ref.get('value'))
        company_info = qb_client.get_company_info()
        
        # Use QuickBooksEfrisMapper to convert
        mapper = QuickBooksEfrisMapper()
        efris_invoice = mapper.qb_invoice_to_efris_t109(
            qb_invoice=qb_invoice,
            qb_customer=qb_customer,
            company_info=company_info,
            tin=company.tin
        )
        
        # Submit to EFRIS
        result = manager.upload_invoice(efris_invoice)
        
        return {
            "message": "Invoice synced successfully",
            "invoiceNo": qb_invoice.get('DocNumber'),
            "efrisResponse": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-invoice/{invoice_id}")
async def get_qb_invoice_details(
    company_id: int,
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get full QuickBooks invoice details with enriched item data"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get invoice from QuickBooks
        qb_invoice = qb_client.get_invoice_by_id(invoice_id)
        
        # Fetch TaxCode definitions from QuickBooks to get actual names
        print(f"[INVOICE] Fetching TaxCode definitions from QuickBooks...")
        tax_code_names = {}  # Maps TaxCode ID to name
        try:
            # Query all TaxCodes
            tax_codes = qb_client.get_tax_codes()
            for tax_code in tax_codes:
                tax_code_id = tax_code.get('Id')
                tax_code_name = tax_code.get('Name', '')
                if tax_code_id:
                    tax_code_names[tax_code_id] = tax_code_name.upper()
                    print(f"[INVOICE] TaxCode {tax_code_id}: '{tax_code_name}'")
        except Exception as e:
            print(f"[INVOICE] Could not fetch TaxCodes: {e}")
        
        # Build a map of TaxCodeRef value to actual tax rate from TxnTaxDetail (UK tax handling)
        tax_rate_map = {}
        if 'TxnTaxDetail' in qb_invoice and 'TaxLine' in qb_invoice['TxnTaxDetail']:
            print(f"[INVOICE] Building tax rate map from TxnTaxDetail...")
            for tax_line in qb_invoice['TxnTaxDetail']['TaxLine']:
                if tax_line.get('DetailType') == 'TaxLineDetail':
                    tax_detail = tax_line.get('TaxLineDetail', {})
                    
                    # Get both TaxRateRef and TaxCodeRef
                    tax_rate_ref = tax_detail.get('TaxRateRef', {})
                    tax_rate_ref_value = tax_rate_ref.get('value')
                    tax_rate_ref_name = tax_rate_ref.get('name', '')
                    
                    tax_code_ref = tax_detail.get('TaxCodeRef', {})
                    tax_code_ref_value = tax_code_ref.get('value')
                    tax_code_ref_name = tax_code_ref.get('name', '')
                    
                    tax_percent = tax_detail.get('TaxPercent', 0)
                    
                    # Map both TaxRateRef.value AND TaxCodeRef.value to the tax percentage
                    if tax_rate_ref_value:
                        tax_rate_map[tax_rate_ref_value] = tax_percent / 100
                        print(f"[INVOICE] Tax map: TaxRate {tax_rate_ref_value} ({tax_rate_ref_name}) = {tax_percent}%")
                    
                    if tax_code_ref_value:
                        tax_rate_map[tax_code_ref_value] = tax_percent / 100
                        print(f"[INVOICE] Tax map: TaxCode {tax_code_ref_value} ({tax_code_ref_name}) = {tax_percent}%")
        
        print(f"[INVOICE] Tax rate map built with {len(tax_rate_map)} entries")
        
        # Load ALL excise codes once for this company (performance optimization)
        excise_reference = load_excise_duty_reference_from_db(company_id, db)
        
        # Enrich line items with EFRIS metadata from database
        if 'Line' in qb_invoice:
            for line in qb_invoice['Line']:
                if line.get('DetailType') == 'SalesItemLineDetail':
                    detail = line.get('SalesItemLineDetail', {})
                    item_ref = detail.get('ItemRef', {})
                    qb_item_id = item_ref.get('value')
                    
                    if qb_item_id:
                        # Get item from database
                        product = db.query(Product).filter(
                            Product.company_id == company_id,
                            Product.qb_item_id == qb_item_id
                        ).first()
                        
                        if product:
                            # Get actual tax rate from QuickBooks
                            tax_code_ref = detail.get('TaxCodeRef', {})
                            tax_code_value = tax_code_ref.get('value')
                            tax_code_name_from_ref = tax_code_ref.get('name', '').upper()
                            
                            # Look up the actual TaxCode name from QuickBooks API
                            tax_code_name = tax_code_names.get(tax_code_value, tax_code_name_from_ref)
                            
                            print(f"[INVOICE] Item {product.qb_name}: TaxCodeRef value='{tax_code_value}', name='{tax_code_name}'")
                            
                            # Priority 1: Check TaxCode name for EXEMPT keyword (highest priority)
                            if 'EXEMPT' in tax_code_name:
                                # Tax Exempt → EFRIS Code 03
                                tax_rate = 0.0
                                print(f"[INVOICE] Item {product.qb_name}: Detected EXEMPT from TaxCodeName: {tax_code_name}")
                            # Priority 2: Check for ZERO-RATED keywords (before generic 0%)
                            elif 'ZERO' in tax_code_name or tax_code_name in ['0.0% Z', '0.0% ECG', '0.0% ECS']:
                                # Zero-Rated 0% → EFRIS Code 02
                                tax_rate = 0.0
                                print(f"[INVOICE] Item {product.qb_name}: Detected ZERO-RATED from TaxCodeName: {tax_code_name}")
                            # Priority 3: Try tax rate map from TxnTaxDetail (UK format)
                            elif tax_code_value and tax_code_value in tax_rate_map:
                                tax_rate = tax_rate_map[tax_code_value]
                                print(f"[INVOICE] Item {product.qb_name}: Tax rate from map: {tax_rate*100}%")
                            else:
                                # Priority 3: Default to Standard 18% VAT → EFRIS Code 01
                                tax_rate = 0.18
                                print(f"[INVOICE] Item {product.qb_name}: Using Standard 18% VAT (TaxCodeName: {tax_code_name})")
                            
                            # Determine IsExempt and IsZeroRated
                            # Priority 1: Use saved database values (user explicitly set these in control panel)
                            # Priority 2: Fall back to detection from QuickBooks TaxCodeName
                            is_exempt_from_db = product.is_exempt or False
                            is_zero_rated_from_db = product.is_zero_rated or False
                            is_exempt_from_qb = 'EXEMPT' in tax_code_name
                            is_zero_rated_from_qb = 'ZERO' in tax_code_name or tax_code_name in ['0.0% Z', '0.0% ECG', '0.0% ECS']
                            
                            # Use database values if set, otherwise use QB detection
                            # Database values take priority because user explicitly saved them
                            if is_exempt_from_db or is_zero_rated_from_db:
                                # User has explicitly set tax category in control panel
                                is_exempt_detected = is_exempt_from_db
                                is_zero_rated_detected = is_zero_rated_from_db
                                print(f"[INVOICE] Item {product.qb_name}: Using DB tax flags - IsExempt={is_exempt_detected}, IsZeroRated={is_zero_rated_detected}")
                            else:
                                # Fall back to QB TaxCodeName detection
                                is_exempt_detected = is_exempt_from_qb
                                is_zero_rated_detected = is_zero_rated_from_qb
                                print(f"[INVOICE] Item {product.qb_name}: Using QB tax flags - IsExempt={is_exempt_detected}, IsZeroRated={is_zero_rated_detected}")
                            
                            # Add enriched metadata
                            detail['ItemDetails'] = {
                                'Name': product.qb_name,
                                'Description': product.qb_description,
                                'Sku': product.qb_sku,
                                'UnitOfMeasure': product.efris_unit_of_measure or '101',
                                'TaxRate': tax_rate,  # Actual tax rate from QuickBooks (US or UK)
                                'TaxCodeName': tax_code_name,  # Tax code name for frontend (EXEMPT, ZERO-RATED, etc.)
                                'HasExcise': product.has_excise or False,
                                'ExciseDutyCode': product.excise_duty_code or '',
                                'ExciseUnit': product.efris_unit_of_measure or '101',
                                'ExciseRate': '0',  # Will be populated below
                                'ExciseRule': '2',  # Will be populated below
                                'IsDeemedVAT': False,  # Can be enriched if needed
                                'VATProjectId': '',
                                'VATProjectName': '',
                                'IsZeroRated': is_zero_rated_detected,  # From detected TaxCodeName
                                'IsExempt': is_exempt_detected  # From detected TaxCodeName
                            }
                            
                            # If has excise, lookup from cached excise reference (O(1) instead of 3 DB queries)
                            if product.has_excise and product.excise_duty_code:
                                excise_data = excise_reference.get(product.excise_duty_code, {})
                                
                                detail['ItemDetails']['ExciseRate'] = excise_data.get('rate', '0')
                                detail['ItemDetails']['ExciseRule'] = excise_data.get('rule', '2')
                                detail['ItemDetails']['ExciseUnit'] = excise_data.get('unit', '101')
                                
                                print(f"[INVOICE] Enriched {product.qb_name} with excise: code={product.excise_duty_code}, rate={excise_data.get('rate')}, rule={excise_data.get('rule')}, unit={excise_data.get('unit')}")
        
        return qb_invoice
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] get_qb_invoice_details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error fetching invoice: {str(e)}")


@app.post("/api/companies/{company_id}/invoices/submit-to-efris")
async def submit_invoice_to_efris(
    company_id: int,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit invoice to EFRIS with T109"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        invoice_id = payload.get('invoice_id')
        invoice_data = payload.get('invoice_data')
        
        if not invoice_id or not invoice_data:
            raise HTTPException(status_code=400, detail="Missing invoice_id or invoice_data")
        
        # Extract line item tax categories from payload (sent from UI)
        line_item_tax_categories = invoice_data.get('LineItemTaxCategories', {})
        print(f"[SUBMIT] Line item tax categories: {line_item_tax_categories}")
        
        # Enrich invoice line items with product metadata (excise rate, unit, tax flags, etc.)
        line_items = invoice_data.get('Line', [])
        for line in line_items:
            if line.get('DetailType') == 'SalesItemLineDetail':
                detail = line.get('SalesItemLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                qb_item_id = item_ref.get('value')
                
                if qb_item_id:
                    # Fetch product metadata from database
                    product = db.query(Product).filter(
                        Product.company_id == company_id,
                        Product.qb_item_id == qb_item_id
                    ).first()
                    
                    if product:
                        # Initialize ItemDetails
                        if 'ItemDetails' not in detail:
                            detail['ItemDetails'] = {}
                        
                        # Add tax flags (CRITICAL for proper tax calculation)
                        detail['ItemDetails']['IsExempt'] = product.is_exempt if product.is_exempt is not None else False
                        detail['ItemDetails']['IsZeroRated'] = product.is_zero_rated if product.is_zero_rated is not None else False
                        # Default tax rate: 0% if exempt/zero-rated, 18% otherwise
                        default_tax_rate = 0.0 if (product.is_exempt or product.is_zero_rated) else 0.18
                        detail['ItemDetails']['TaxRate'] = default_tax_rate
                        
                        print(f"[SUBMIT] Product {product.qb_name or product.qb_item_id}: IsExempt={detail['ItemDetails']['IsExempt']}, IsZeroRated={detail['ItemDetails']['IsZeroRated']}, TaxRate={detail['ItemDetails']['TaxRate']}")
                        
                        # Add excise info if applicable
                        if product.has_excise:
                            excise_rate = get_excise_rate(product.excise_duty_code, company_id, db) if product.excise_duty_code else '0'
                            excise_rule = get_excise_rule(product.excise_duty_code, company_id, db) if product.excise_duty_code else '2'
                            
                            detail['ItemDetails']['HasExcise'] = True
                            detail['ItemDetails']['ExciseDutyCode'] = product.excise_duty_code
                            detail['ItemDetails']['ExciseUnit'] = product.excise_unit or get_excise_unit(product.excise_duty_code, company_id, db)
                            detail['ItemDetails']['ExciseRate'] = excise_rate
                            detail['ItemDetails']['ExciseRule'] = excise_rule
                        else:
                            detail['ItemDetails']['HasExcise'] = False
        
        # Get customer details
        customer_ref = invoice_data.get('CustomerRef', {})
        customer_id = customer_ref.get('value')
        
        # Try to fetch customer from QuickBooks, fallback to invoice data
        qb_customer = {}
        if customer_id:
            try:
                print(f"[SUBMIT] Fetching customer {customer_id} from QuickBooks...")
                qb_customer = qb_client.get_customer_by_id(customer_id)
                print(f"[SUBMIT] Customer fetched successfully: {qb_customer.get('DisplayName', 'N/A')}")
            except Exception as e:
                print(f"[SUBMIT] Warning: Could not fetch customer from QuickBooks: {e}")
                # Use customer name from invoice if available
                qb_customer = {
                    'DisplayName': customer_ref.get('name', 'Customer'),
                    'CompanyName': customer_ref.get('name', ''),
                    'PrimaryEmailAddr': {},
                    'PrimaryPhone': {}
                }
        else:
            print("[SUBMIT] Warning: No customer ID in invoice")
            qb_customer = {
                'DisplayName': 'Walk-in Customer',
                'CompanyName': '',
                'PrimaryEmailAddr': {},
                'PrimaryPhone': {}
            }
        
        # Get company info
        company_dict = {
            'EfrisTin': company.tin,
            'CompanyName': company.name,
            'EfrisDeviceNo': company.device_no,
            'PrimaryPhone': {'FreeFormNumber': '0700000000'},
            'Email': {'Address': 'info@wandera.com'},
            'CompanyAddr': {'Line1': 'Kampala, Uganda'},
            'Country': 'Uganda',
            'qb_region': company.qb_region  # Add region for validation
        }
        
        # Get line item tax categories if provided (optional - will auto-detect from QB if not provided)
        line_item_tax_categories = invoice_data.get('LineItemTaxCategories', None)
        
        # Convert to EFRIS format using mapper
        mapper = QuickBooksEfrisMapper()
        efris_invoice = mapper.map_invoice_to_efris(
            qb_invoice=invoice_data,
            qb_customer=qb_customer,
            company_info=company_dict,
            line_item_tax_categories=line_item_tax_categories  # Pass tax categories (optional)
        )
        
        # Submit to EFRIS via T109
        result = manager.upload_invoice(efris_invoice)
        
        # Parse response
        return_code = result.get('returnStateInfo', {}).get('returnCode')
        print(f"[SUBMIT] Return code: {return_code}")
        print(f"[SUBMIT] Return message: {result.get('returnStateInfo', {}).get('returnMessage', '')}")
        print(f"[SUBMIT] Result keys: {result.keys()}")
        print(f"[SUBMIT] Data keys: {result.get('data', {}).keys()}")
        
        # Handle success (00) or already fiscalized (2253)
        if return_code == '00' or return_code == '2253':
            # Success - extract FDN from decrypted content
            data = result.get('data', {})
            decrypted_content = data.get('decrypted_content', {})
            
            # Check if this is a duplicate (code 2253)
            if return_code == '2253':
                # Already fiscalized - extract FDN from existInvoiceList
                exist_list = decrypted_content.get('existInvoiceList', [])
                if exist_list and len(exist_list) > 0:
                    fdn = exist_list[0].get('invoiceNo', '')
                    antifake_code = exist_list[0].get('antiFakeCode', '')
                    efris_invoice_id = ''  # Not provided in duplicate response
                    print(f"[SUBMIT] Already fiscalized - FDN: {fdn}, Antifake: {antifake_code}")
                else:
                    fdn = ''
                    antifake_code = ''
                    efris_invoice_id = ''
            else:
                # New invoice - extract from basicInformation section
                basic_info = decrypted_content.get('basicInformation', {})
                fdn = basic_info.get('invoiceNo', '') or decrypted_content.get('fdn', '') or data.get('fdn', '')
                efris_invoice_id = basic_info.get('invoiceId', '') or decrypted_content.get('invoiceId', '') or data.get('invoiceId', '')
                antifake_code = basic_info.get('antifakeCode', '')
            
            print(f"[SUBMIT] FDN: {fdn}")
            print(f"[SUBMIT] Invoice ID: {efris_invoice_id}")
            print(f"[SUBMIT] Antifake Code: {antifake_code}")
            
            # Save to database
            efris_inv = db.query(EFRISInvoice).filter(
                EFRISInvoice.company_id == company_id,
                EFRISInvoice.qb_invoice_id == invoice_id
            ).first()
            
            # Convert invoice_date to date object if it's a string
            invoice_date = invoice_data.get('TxnDate')
            if isinstance(invoice_date, str):
                invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            
            # Extract additional details from the decrypted_content if available
            buyer_legal_name = None
            buyer_business_name = None
            buyer_tin_efris = None
            currency = None
            gross_amount = None
            tax_amount = None
            net_amount = None
            
            if return_code == '00':
                # For new invoices, extract from basicInformation and other sections
                buyer_details = decrypted_content.get('buyerDetails', {})
                summary = decrypted_content.get('summary', {})
                tax_details_raw = decrypted_content.get('taxDetails', {})
                # Handle taxDetails as either dict or list
                tax_details = tax_details_raw if isinstance(tax_details_raw, dict) else {}
                basic_info = decrypted_content.get('basicInformation', {})
                
                buyer_legal_name = buyer_details.get('buyerLegalName')
                buyer_business_name = buyer_details.get('buyerBusinessName')
                buyer_tin_efris = buyer_details.get('buyerTin')
                currency = basic_info.get('currency')
                gross_amount = float(summary.get('grossAmount', 0)) if summary.get('grossAmount') else float(invoice_data.get('TotalAmt', 0))
                tax_amount = float(tax_details.get('taxAmount', 0)) if tax_details.get('taxAmount') else None
                net_amount = float(tax_details.get('netAmount', 0)) if tax_details.get('netAmount') else None
            
            if not efris_inv:
                efris_inv = EFRISInvoice(
                    company_id=company_id,
                    qb_invoice_id=invoice_id,
                    qb_invoice_number=invoice_data.get('DocNumber', ''),
                    invoice_date=invoice_date,
                    customer_name=qb_customer.get('DisplayName', ''),
                    customer_tin=invoice_data.get('BuyerTin', ''),
                    buyer_type=invoice_data.get('BuyerType', '1'),
                    total_amount=float(invoice_data.get('TotalAmt', 0)),
                    status='success',
                    fdn=fdn,
                    invoice_no=fdn,
                    efris_invoice_id=efris_invoice_id,
                    buyer_legal_name=buyer_legal_name or qb_customer.get('DisplayName', ''),
                    buyer_business_name=buyer_business_name or qb_customer.get('CompanyName', ''),
                    buyer_tin=buyer_tin_efris,
                    currency=currency or 'UGX',
                    gross_amount=gross_amount or float(invoice_data.get('TotalAmt', 0)),
                    tax_amount=tax_amount,
                    net_amount=net_amount,
                    efris_payload=efris_invoice,
                    efris_response=result
                )
                db.add(efris_inv)
            else:
                efris_inv.status = 'success'
                efris_inv.fdn = fdn
                efris_inv.efris_invoice_id = efris_invoice_id
                efris_inv.efris_payload = efris_invoice
                efris_inv.efris_response = result
                efris_inv.error_message = None
                efris_inv.invoice_no = fdn
                
                # Update details if available
                if buyer_legal_name:
                    efris_inv.buyer_legal_name = buyer_legal_name
                if buyer_business_name:
                    efris_inv.buyer_business_name = buyer_business_name
                if buyer_tin_efris:
                    efris_inv.buyer_tin = buyer_tin_efris
                if currency:
                    efris_inv.currency = currency
                if gross_amount:
                    efris_inv.gross_amount = gross_amount
                if tax_amount is not None:
                    efris_inv.tax_amount = tax_amount
                if net_amount is not None:
                    efris_inv.net_amount = net_amount
            
            db.commit()
            
            return {
                "success": True,
                "fdn": fdn,
                "efris_invoice_id": efris_invoice_id,
                "antifake_code": antifake_code,
                "efris_invoice": decrypted_content,
                "message": "Invoice submitted successfully"
            }
        else:
            # Failed
            error_msg = result.get('returnStateInfo', {}).get('returnMessage', 'Unknown error')
            
            # Save error to database
            efris_inv = db.query(EFRISInvoice).filter(
                EFRISInvoice.company_id == company_id,
                EFRISInvoice.qb_invoice_id == invoice_id
            ).first()
            
            # Convert invoice_date to date object if it's a string
            invoice_date = invoice_data.get('TxnDate')
            if isinstance(invoice_date, str):
                invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            
            if not efris_inv:
                efris_inv = EFRISInvoice(
                    company_id=company_id,
                    qb_invoice_id=invoice_id,
                    qb_invoice_number=invoice_data.get('DocNumber', ''),
                    invoice_date=invoice_date,
                    customer_name=qb_customer.get('DisplayName', ''),
                    customer_tin=invoice_data.get('BuyerTin', ''),
                    buyer_type=invoice_data.get('BuyerType', '1'),
                    total_amount=float(invoice_data.get('TotalAmt', 0)),
                    status='failed',
                    error_message=error_msg,
                    efris_payload=efris_invoice,
                    efris_response=result
                )
                db.add(efris_inv)
            else:
                efris_inv.status = 'failed'
                efris_inv.error_message = error_msg
                efris_inv.efris_payload = efris_invoice
                efris_inv.efris_response = result
            
            db.commit()
            
            return {
                "success": False,
                "error": error_msg,
                "return_code": return_code,
                "efris_response": result
            }
            
    except Exception as e:
        print(f"Invoice submission error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/credit-memos")
async def get_quickbooks_credit_memos(
    company_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch credit memos from QuickBooks"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        credit_memos = qb_client.get_credit_memos(start_date=start_date, end_date=end_date)
        return {
            "count": len(credit_memos),
            "creditMemos": credit_memos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/purchase-orders")
async def get_quickbooks_purchase_orders(
    company_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch purchase orders from QuickBooks"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        purchase_orders = qb_client.get_purchase_orders(start_date=start_date, end_date=end_date)
        return {
            "count": len(purchase_orders),
            "purchase_orders": purchase_orders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/sync-purchase-orders")
async def sync_purchase_orders_to_efris(
    company_id: int = Query(...),
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync purchase orders from QuickBooks to EFRIS as stock increases"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        qb_pos = payload.get('purchase_orders', [])
        if not qb_pos:
            raise HTTPException(status_code=400, detail="No purchase orders provided")
        
        synced_count = 0
        failed = []
        
        for po_data in qb_pos:
            try:
                # Get vendor details
                vendor = {}
                if 'VendorRef' in po_data:
                    try:
                        vendor = qb_client.get_vendor_by_id(po_data['VendorRef']['value'])
                    except:
                        vendor = {'DisplayName': po_data['VendorRef'].get('name', 'Unknown')}
                
                # Convert to EFRIS stock increase format
                stock_data = {
                    "goodsStockIn": {
                        "operationType": "101",
                        "supplierTin": "",
                        "supplierName": vendor.get('DisplayName', 'Unknown'),
                        "remarks": f"PO {po_data.get('DocNumber', '')}",
                        "stockInDate": po_data.get('TxnDate', ''),
                        "stockInType": "102"
                    },
                    "goodsStockInItem": []
                }
                
                for line in po_data.get('Line', []):
                    if line.get('DetailType') == 'ItemBasedExpenseLineDetail':
                        detail = line.get('ItemBasedExpenseLineDetail', {})
                        item_ref = detail.get('ItemRef', {})
                        
                        stock_data["goodsStockInItem"].append({
                            "goodsCode": item_ref.get('name', ''),
                            "quantity": detail.get('Qty', 0),
                            "unitPrice": detail.get('UnitPrice', 0)
                        })
                
                if stock_data["goodsStockInItem"]:
                    result = manager.stock_increase(stock_data)
                    if result.get('returnStateInfo', {}).get('returnCode') == '00':
                        synced_count += 1
                    else:
                        failed.append({
                            "po": po_data.get('DocNumber'),
                            "error": result.get('returnStateInfo', {}).get('returnMessage')
                        })
            except Exception as e:
                failed.append({
                    "po": po_data.get('DocNumber'),
                    "error": str(e)
                })
        
        return {
            "synced_count": synced_count,
            "failed_count": len(failed),
            "failed": failed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== DATABASE CRUD for QB DATA ==========

@app.post("/api/companies/{company_id}/qb-purchase-orders/import")
async def import_qb_purchase_orders_to_db(
    company_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch QB purchase orders and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Fetch from QuickBooks
        pos = qb_client.get_purchase_orders(start_date=start_date, end_date=end_date)
        
        saved_count = 0
        for po in pos:
            # Check if already exists
            existing = db.query(PurchaseOrder).filter(
                PurchaseOrder.company_id == company_id,
                PurchaseOrder.qb_po_id == po.get('Id')
            ).first()
            
            # Parse transaction date
            txn_date = None
            if po.get('TxnDate'):
                try:
                    txn_date = datetime.strptime(po['TxnDate'], '%Y-%m-%d')
                except:
                    pass
            
            if existing:
                # Update existing
                existing.qb_doc_number = po.get('DocNumber')
                existing.qb_vendor_name = po.get('VendorRef', {}).get('name')
                existing.qb_txn_date = txn_date
                existing.qb_total_amt = float(po.get('TotalAmt', 0))
                existing.qb_data = po
                existing.updated_at = datetime.now()
            else:
                # Create new
                purchase_order = PurchaseOrder(
                    company_id=company_id,
                    qb_po_id=po.get('Id'),
                    qb_doc_number=po.get('DocNumber'),
                    qb_vendor_name=po.get('VendorRef', {}).get('name'),
                    qb_txn_date=txn_date,
                    qb_total_amt=float(po.get('TotalAmt', 0)),
                    qb_data=po
                )
                db.add(purchase_order)
                saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {len(pos)} purchase orders ({saved_count} new, {len(pos)-saved_count} updated)",
            "count": len(pos)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-purchase-orders")
async def get_saved_qb_purchase_orders(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get QB purchase orders saved in database with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (PurchaseOrder.qb_doc_number.ilike(search_pattern)) |
            (PurchaseOrder.qb_vendor_name.ilike(search_pattern))
        )
    
    pos = query.order_by(PurchaseOrder.qb_txn_date.desc()).all()
    
    result = []
    for po in pos:
        result.append({
            "id": po.id,
            "qb_po_id": po.qb_po_id,
            "doc_number": po.qb_doc_number,
            "vendor_name": po.qb_vendor_name,
            "txn_date": po.qb_txn_date.strftime('%Y-%m-%d') if po.qb_txn_date else None,
            "total_amt": po.qb_total_amt,
            "qb_data": po.qb_data,
            "efris_status": po.efris_status or "pending",
            "efris_sent_at": po.efris_sent_at.isoformat() if po.efris_sent_at else None,
            "efris_error": po.efris_error,
            "created_at": po.created_at.isoformat() if po.created_at else None
        })
    
    return result


@app.post("/api/companies/{company_id}/qb-purchase-orders/sync-to-efris")
async def sync_selected_purchase_orders_to_efris(
    company_id: int,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send selected purchase orders to EFRIS as stock increases (T131)"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        po_ids = payload.get('po_ids', [])
        if not po_ids:
            raise HTTPException(status_code=400, detail="No purchase order IDs provided")
        
        # Get the selected purchase orders from database
        pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.id.in_(po_ids)
        ).all()
        
        if not pos:
            raise HTTPException(status_code=404, detail="No purchase orders found")
        
        synced_count = 0
        failed = []
        
        for po in pos:
            try:
                po_data = po.qb_data
                
                # Get vendor details from QuickBooks
                vendor = {}
                vendor_ref = po_data.get('VendorRef', {})
                if vendor_ref and vendor_ref.get('value'):
                    try:
                        vendor = qb_client.get_vendor_by_id(vendor_ref['value'])
                    except:
                        vendor = {'DisplayName': vendor_ref.get('name', 'Unknown')}
                else:
                    vendor = {'DisplayName': po.qb_vendor_name or 'Unknown'}
                
                # Convert to EFRIS stock increase format (T131)
                stock_data = {
                    "goodsStockIn": {
                        "operationType": "101",  # 101 = Stock increase
                        "supplierTin": "",  # Supplier TIN (optional)
                        "supplierName": vendor.get('DisplayName', 'Unknown'),
                        "remarks": f"QuickBooks PO #{po.qb_doc_number}",
                        "stockInDate": po.qb_txn_date.strftime('%Y-%m-%d') if po.qb_txn_date else datetime.now().strftime('%Y-%m-%d'),
                        "stockInType": "102",  # 102 = Purchase
                        "isCheckBatchNo": "0",
                        "rollBackIfError": "0"
                    },
                    "goodsStockInItem": []
                }
                
                # Process line items
                for line in po_data.get('Line', []):
                    detail_type = line.get('DetailType')
                    
                    # Handle both ItemBasedExpenseLineDetail and AccountBasedExpenseLineDetail
                    if detail_type == 'ItemBasedExpenseLineDetail':
                        detail = line.get('ItemBasedExpenseLineDetail', {})
                        item_ref = detail.get('ItemRef', {})
                        
                        # Get item details to find the product code
                        item_id = item_ref.get('value')
                        item_name = item_ref.get('name', '')
                        goods_code = item_name  # Default fallback
                        
                        # Try to get the product from our database first
                        if item_id:
                            product = db.query(Product).filter(
                                Product.company_id == company_id,
                                Product.qb_item_id == item_id
                            ).first()
                            
                            if product and product.qb_description:
                                goods_code = product.qb_description
                            else:
                                # If not in database, try fetching from QuickBooks
                                try:
                                    qb_item = qb_client.get_item_by_id(item_id)
                                    # Use Description field as product code
                                    if qb_item.get('Description'):
                                        goods_code = qb_item['Description']
                                    print(f"[T131] Item {item_name}: Using code '{goods_code}' from QuickBooks")
                                except Exception as e:
                                    print(f"[T131] Warning: Could not fetch item details from QuickBooks: {e}")
                                    print(f"[T131] Using item name '{item_name}' as fallback")
                        
                        quantity = float(detail.get('Qty', 0))
                        unit_price = float(detail.get('UnitPrice', 0))
                        
                        if quantity > 0:
                            # Format numbers: remove .0 for whole numbers
                            qty_str = str(int(quantity)) if quantity == int(quantity) else str(quantity)
                            price_str = str(int(unit_price)) if unit_price == int(unit_price) else str(unit_price)
                            
                            # Look up EFRIS good to get commodityGoodsId and measureUnit
                            efris_good = db.query(EFRISGood).filter(
                                EFRISGood.company_id == company_id,
                                EFRISGood.goods_code == goods_code
                            ).first()
                            
                            item_data = {
                                "goodsCode": goods_code,
                                "quantity": qty_str,
                                "unitPrice": price_str,
                                "remarks": f"PO #{po.qb_doc_number}"
                            }
                            
                            # Add commodityGoodsId and measureUnit if found in EFRIS
                            if efris_good and efris_good.efris_data:
                                commodity_id = efris_good.efris_data.get('id')
                                measure_unit = efris_good.efris_data.get('measureUnit')
                                if commodity_id:
                                    item_data["commodityGoodsId"] = commodity_id
                                if measure_unit:
                                    item_data["measureUnit"] = measure_unit
                                print(f"[T131] Added item: code={goods_code}, id={commodity_id}, unit={measure_unit}, qty={qty_str}, price={price_str}")
                            else:
                                print(f"[T131] Added item: code={goods_code}, qty={qty_str}, price={price_str} (no EFRIS data)")
                            
                            stock_data["goodsStockInItem"].append(item_data)
                
                # Only send if there are items
                if stock_data["goodsStockInItem"]:
                    print(f"[T131] Sending stock increase to EFRIS...")
                    print(f"[T131] Full payload: {json.dumps(stock_data, indent=2)}")
                    
                    result = manager.stock_increase(stock_data)
                    
                    return_code = result.get('returnStateInfo', {}).get('returnCode')
                    return_msg = result.get('returnStateInfo', {}).get('returnMessage', '')
                    
                    print(f"[T131] Response code: {return_code}, message: {return_msg}")
                    
                    # Check decrypted response
                    decrypted = result.get('data', {}).get('decrypted_content', [])
                    print(f"[T131] Decrypted response: {decrypted}")
                    
                    if return_code == '00':
                        # Update PO status to 'sent'
                        po.efris_status = 'sent'
                        po.efris_sent_at = datetime.now()
                        po.efris_response = result
                        po.efris_error = None
                        synced_count += 1
                        print(f"[T131] ✓ Stock increase successful for PO #{po.qb_doc_number}")
                    else:
                        # Update PO status to 'failed'
                        error_msg = result.get('returnStateInfo', {}).get('returnMessage', 'Unknown error')
                        po.efris_status = 'failed'
                        po.efris_error = error_msg
                        po.efris_response = result
                        failed.append({
                            "po": po.qb_doc_number,
                            "error": error_msg
                        })
                else:
                    # Update PO status to 'failed' - no items
                    po.efris_status = 'failed'
                    po.efris_error = 'No valid line items found'
                    failed.append({
                        "po": po.qb_doc_number,
                        "error": "No valid line items found"
                    })
                    
            except Exception as e:
                # Update PO status to 'failed' on exception
                po.efris_status = 'failed'
                po.efris_error = str(e)
                failed.append({
                    "po": po.qb_doc_number,
                    "error": str(e)
                })
        
        # Commit all status updates
        db.commit()
        
        return {
            "success": True,
            "synced_count": synced_count,
            "failed_count": len(failed),
            "failed": failed,
            "message": f"Successfully sent {synced_count} purchase orders to EFRIS"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/companies/{company_id}/qb-items/import")
async def import_qb_items_to_db(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch QB items and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Fetch from QuickBooks
        items = qb_client.get_all_items()
        
        saved_count = 0
        for item in items:
            # Check if already exists
            existing = db.query(Product).filter(
                Product.company_id == company_id,
                Product.qb_item_id == item.get('Id')
            ).first()
            
            if existing:
                # Update existing
                existing.qb_name = item.get('Name')
                existing.qb_sku = item.get('Sku')
                existing.qb_description = item.get('Description')
                existing.qb_unit_price = float(item.get('UnitPrice', 0))
                existing.qb_type = item.get('Type')
                existing.updated_at = datetime.now()
            else:
                # Create new
                product = Product(
                    company_id=company_id,
                    qb_item_id=item.get('Id'),
                    qb_name=item.get('Name'),
                    qb_sku=item.get('Sku'),
                    qb_description=item.get('Description'),
                    qb_unit_price=float(item.get('UnitPrice', 0)),
                    qb_type=item.get('Type'),
                    efris_status='Pending Registration'
                )
                db.add(product)
                saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {len(items)} items ({saved_count} new, {len(items)-saved_count} updated)",
            "count": len(items)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-items")
async def get_saved_qb_items(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get QB items saved in database with EFRIS registration status and optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(Product).filter(Product.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.qb_name.ilike(search_pattern)) |
            (Product.qb_sku.ilike(search_pattern)) |
            (Product.qb_description.ilike(search_pattern))
        )
    
    products = query.order_by(Product.updated_at.desc()).all()
    
    # Get all EFRIS goods for this company to check registration status
    efris_goods = db.query(EFRISGood).filter(EFRISGood.company_id == company_id).all()
    
    # Create a set of registered product codes for quick lookup
    registered_codes = {good.goods_code.strip().upper() if good.goods_code else '' 
                       for good in efris_goods if good.goods_code}
    
    items_with_status = []
    for p in products:
        # Get the product code from Description field
        product_code = (p.qb_description or '').strip().upper()
        
        # Check if this product code exists in EFRIS
        is_registered = product_code in registered_codes if product_code else False
        
        items_with_status.append({
            "Id": p.qb_item_id,
            "Name": p.qb_name,
            "Sku": p.qb_sku,
            "Description": p.qb_description,
            "UnitPrice": p.qb_unit_price,
            "Type": p.qb_type,
            "EfrisStatus": "Registered" if is_registered else "Pending",
            "EfrisId": p.efris_id,
            "EfrisProductCode": product_code,  # Include for debugging
            "IsZeroRated": p.is_zero_rated or False,  # Tax category: Zero-rated (EFRIS code 02)
            "IsExempt": p.is_exempt or False,  # Tax category: Exempt (EFRIS code 03)
            "HasExcise": p.has_excise or False,
            "ExciseDutyCode": p.excise_duty_code or '',
            "EfrisUnitOfMeasure": p.efris_unit_of_measure or '101',
            "EfrisCommodityCode": p.efris_commodity_code or ''
        })
    
    return {
        "count": len(products),
        "registered_count": sum(1 for item in items_with_status if item["EfrisStatus"] == "Registered"),
        "pending_count": sum(1 for item in items_with_status if item["EfrisStatus"] == "Pending"),
        "items": items_with_status
    }


@app.put("/api/companies/{company_id}/qb-items/{item_id}/efris-metadata")
async def update_item_efris_metadata(
    company_id: int,
    item_id: str,
    metadata: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update EFRIS metadata for a QB item before registration"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Find the product
        product = db.query(Product).filter(
            Product.company_id == company_id,
            Product.qb_item_id == item_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update EFRIS metadata
        if 'efris_commodity_code' in metadata:
            product.efris_commodity_code = metadata['efris_commodity_code']
        if 'efris_unit_of_measure' in metadata:
            product.efris_unit_of_measure = metadata['efris_unit_of_measure']
        if 'has_excise' in metadata:
            product.has_excise = metadata['has_excise']
        if 'excise_duty_code' in metadata:
            product.excise_duty_code = metadata['excise_duty_code']
        if 'efris_product_code' in metadata:
            product.efris_product_code = metadata['efris_product_code']
        if 'is_zero_rated' in metadata:
            product.is_zero_rated = metadata['is_zero_rated']
        if 'is_exempt' in metadata:
            product.is_exempt = metadata['is_exempt']
        
        product.updated_at = datetime.now()
        db.commit()
        
        return {
            "message": "EFRIS metadata updated successfully",
            "product": {
                "id": product.qb_item_id,
                "name": product.qb_name,
                "efris_commodity_code": product.efris_commodity_code,
                "efris_unit_of_measure": product.efris_unit_of_measure,
                "has_excise": product.has_excise,
                "excise_duty_code": product.excise_duty_code,
                "is_zero_rated": product.is_zero_rated,
                "is_exempt": product.is_exempt
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/qb-items/register-to-efris")
async def register_qb_items_to_efris(
    company_id: int,
    item_ids: List[str] = Body(..., embed=True),
    default_category_id: str = Body("50202306"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Register selected QB items to EFRIS"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    manager = get_efris_manager(company)
    
    try:
        # Get the selected products from database
        products = db.query(Product).filter(
            Product.company_id == company_id,
            Product.qb_item_id.in_(item_ids)
        ).all()
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found")
        
        # Convert to EFRIS format
        efris_products = []
        for p in products:
            # Use efris_product_code if set, otherwise Description, fallback to Name
            goods_code = p.efris_product_code or p.qb_description or p.qb_name or ""
            is_service = p.qb_type == "Service"
            unit_price = p.qb_unit_price or 0
            
            # Use saved EFRIS metadata if available
            measure_unit = p.efris_unit_of_measure or ("102" if is_service else "101")
            commodity_code = p.efris_commodity_code or p.qb_sku or default_category_id
            
            # Determine tax category based on product settings (used as DEFAULT during registration)
            # Note: During invoice fiscalization, user can override this per line item
            # 01 = Standard rated (18% VAT)
            # 02 = Zero-rated (0% VAT)
            # 03 = Tax exempt (No VAT)
            if p.is_zero_rated:
                tax_category = "02"
            elif p.is_exempt:
                tax_category = "03"
            else:
                tax_category = "01"  # Default to standard rate
            
            # For excise items, get the required unit from excise duty reference
            piece_measure_unit = measure_unit
            if p.has_excise and p.excise_duty_code:
                excise_unit = get_excise_unit(p.excise_duty_code, company_id, db)
                if excise_unit:  # Use excise unit if available
                    piece_measure_unit = excise_unit
                    print(f"[T130] Excise item: {p.qb_name} - using excise unit: {excise_unit} for pieceMeasureUnit")
            
            # Check if item already exists in EFRIS by checking EFRISGood table
            existing_efris_good = db.query(EFRISGood).filter(
                EFRISGood.company_id == company_id,
                EFRISGood.goods_code == goods_code
            ).first()
            
            # Use operationType 102 (update) if exists, 101 (new) if not
            operation_type = "102" if existing_efris_good else "101"
            
            efris_product = {
                "operationType": operation_type,
                "goodsName": p.qb_name or "",
                "goodsCode": goods_code,
                "measureUnit": measure_unit,
                "unitPrice": str(unit_price),
                "currency": "101",  # UGX
                "commodityCategoryId": commodity_code,
                "haveExciseTax": "101" if p.has_excise else "102",
                "taxCategoryCode": tax_category,  # 01=Standard, 02=Zero-rated, 03=Exempt
                "goodsTypeCode": "101",  # Always 101 for goods/services (102 is for fuel)
                "serviceMark": "101" if is_service else "102",  # 101=Service, 102=Goods
                "description": goods_code,
                "havePieceUnit": "101",
                "pieceMeasureUnit": piece_measure_unit,  # Use excise unit if excise item
                "pieceUnitPrice": str(unit_price),
                "packageScaledValue": "1",
                "pieceScaledValue": "1"
            }
            
            # Stock settings
            # Note: T130 doesn't allow opening stock (must be set via T131 after registration)
            opening_stock = 0
            if is_service:
                efris_product["stockPrewarning"] = "0"
                efris_product["stockPrequantity"] = "0"  # Services don't have stock
            else:
                efris_product["stockPrewarning"] = "10"
                # Note: EFRIS doesn't allow opening stock in T130, must use T131 after registration
                efris_product["stockPrequantity"] = "0"  # Always 0 for T130
            
            # Excise duty
            if p.has_excise and p.excise_duty_code:
                efris_product["exciseDutyCode"] = p.excise_duty_code
            
            efris_products.append(efris_product)
        
        # Upload to EFRIS
        result = manager.upload_goods(efris_products)
        
        # Check if successful and update database
        success_count = 0
        failed_items = []
        items_to_retry = []
        
        print(f"[Register Items] EFRIS Response: {json.dumps(result, indent=2)[:1000]}")
        
        # Check for partial failure (returnCode 45) or success (00)
        return_code = result.get('returnStateInfo', {}).get('returnCode')
        
        if return_code in ['00', '45']:  # Success or partial failure
            # Parse the decrypted content to get individual item results
            decrypted = result.get('data', {}).get('decrypted_content', [])
            
            print(f"[Register Items] Decrypted content type: {type(decrypted)}")
            print(f"[Register Items] Decrypted content: {decrypted}")
            
            if isinstance(decrypted, list):
                # If empty array and return code is 00, all items succeeded
                if len(decrypted) == 0 and return_code == '00':
                    print(f"[Register Items] Empty response with code 00 - all items succeeded")
                    for idx, product in enumerate(products):
                        product.efris_status = "Registered"
                        product.efris_product_code = efris_products[idx]['goodsCode']
                        success_count += 1
                        
                        # Update or create EFRISGood
                        efris_good = db.query(EFRISGood).filter(
                            EFRISGood.company_id == company_id,
                            EFRISGood.goods_code == efris_products[idx]['goodsCode']
                        ).first()
                        
                        if efris_good:
                            # Update existing
                            efris_good.goods_name = efris_products[idx]['goodsName']
                            efris_good.unit_price = float(efris_products[idx]['unitPrice'])
                        else:
                            # Create new
                            efris_good = EFRISGood(
                                company_id=company_id,
                                goods_code=efris_products[idx]['goodsCode'],
                                goods_name=efris_products[idx]['goodsName'],
                                commodity_category_code=efris_products[idx]['commodityCategoryId'],
                                commodity_category_name="",
                                unit_price=float(efris_products[idx]['unitPrice']),
                                currency="UGX",
                                tax_rate=0.18,
                                have_excise_tax=efris_products[idx]['haveExciseTax'],
                                stock=0,
                                efris_data={}
                            )
                            db.add(efris_good)
                
                for idx, item_result in enumerate(decrypted):
                    if idx < len(products):
                        product = products[idx]
                        
                        result_code = item_result.get('resultCode') or item_result.get('returnCode')
                        result_msg = item_result.get('resultMsg') or item_result.get('returnMessage')
                        
                        print(f"[Register Items] Item {idx}: {product.qb_name} - Code: {result_code}, Msg: {result_msg}")
                        
                        # Check if this specific item succeeded
                        if result_code == '00' or result_msg == 'SUCCESS':
                            # Update product status in database
                            product.efris_status = "Registered"
                            product.efris_id = item_result.get('id', '')
                            product.efris_product_code = efris_products[idx]['goodsCode']
                            success_count += 1
                            
                            # Also save to EFRISGood table
                            efris_good = db.query(EFRISGood).filter(
                                EFRISGood.company_id == company_id,
                                EFRISGood.goods_code == efris_products[idx]['goodsCode']
                            ).first()
                            
                            if not efris_good:
                                efris_good = EFRISGood(
                                    company_id=company_id,
                                    goods_code=efris_products[idx]['goodsCode'],
                                    goods_name=efris_products[idx]['goodsName'],
                                    commodity_category_code=efris_products[idx]['commodityCategoryId'],
                                    commodity_category_name="",
                                    unit_price=float(efris_products[idx]['unitPrice']),
                                    currency="UGX",
                                    tax_rate=0.18,  # Default 18%
                                    have_excise_tax=efris_products[idx]['haveExciseTax'],
                                    stock=0,
                                    efris_data=item_result
                                )
                                db.add(efris_good)
                        elif result_code == '602':
                            # Item already exists, retry with operationType 102
                            print(f"[Register Items] Item already exists, will retry with update (operationType 102)")
                            retry_product = efris_products[idx].copy()
                            retry_product['operationType'] = '102'
                            items_to_retry.append((idx, product, retry_product))
                        else:
                            failed_items.append({
                                "name": product.qb_name,
                                "error": result_msg or 'Unknown error'
                            })
            
            # Retry items that returned 602 with operationType 102
            if items_to_retry:
                print(f"[Register Items] Retrying {len(items_to_retry)} items with operationType 102")
                retry_products_list = [item[2] for item in items_to_retry]
                retry_result = manager.upload_goods(retry_products_list)
                
                print(f"[Register Items] Retry result: {json.dumps(retry_result, indent=2)[:1000]}")
                
                if retry_result.get('returnStateInfo', {}).get('returnCode') in ['00', '45']:
                    retry_decrypted = retry_result.get('data', {}).get('decrypted_content', [])
                    
                    # Handle empty array response (means all succeeded)
                    if isinstance(retry_decrypted, list):
                        # If decrypted is empty list, it means success for all items
                        if len(retry_decrypted) == 0 and retry_result.get('returnStateInfo', {}).get('returnCode') == '00':
                            print(f"[Register Items] Retry successful (empty response means success)")
                            for retry_idx, (orig_idx, product, retry_product) in enumerate(items_to_retry):
                                product.efris_status = "Registered"
                                product.efris_product_code = retry_product['goodsCode']
                                success_count += 1
                                
                                # Update or create EFRISGood
                                efris_good = db.query(EFRISGood).filter(
                                    EFRISGood.company_id == company_id,
                                    EFRISGood.goods_code == retry_product['goodsCode']
                                ).first()
                                
                                if efris_good:
                                    # Update existing
                                    efris_good.goods_name = retry_product['goodsName']
                                    efris_good.unit_price = float(retry_product['unitPrice'])
                                else:
                                    # Create new
                                    efris_good = EFRISGood(
                                        company_id=company_id,
                                        goods_code=retry_product['goodsCode'],
                                        goods_name=retry_product['goodsName'],
                                        commodity_category_code=retry_product['commodityCategoryId'],
                                        commodity_category_name="",
                                        unit_price=float(retry_product['unitPrice']),
                                        currency="UGX",
                                        tax_rate=0.18,
                                        have_excise_tax=retry_product['haveExciseTax'],
                                        stock=0,
                                        efris_data={}
                                    )
                                    db.add(efris_good)
                                
                                # Remove from failed items if it was added
                                failed_items = [f for f in failed_items if f.get('name') != product.qb_name]
                        else:
                            # Process individual retry results
                            for retry_idx, (orig_idx, product, retry_product) in enumerate(items_to_retry):
                                if retry_idx < len(retry_decrypted):
                                    retry_item_result = retry_decrypted[retry_idx]
                                    retry_code = retry_item_result.get('resultCode') or retry_item_result.get('returnCode')
                                    retry_msg = retry_item_result.get('resultMsg') or retry_item_result.get('returnMessage')
                                    
                                    if retry_code == '00' or retry_msg == 'SUCCESS':
                                        product.efris_status = "Registered"
                                        product.efris_id = retry_item_result.get('id', '')
                                        product.efris_product_code = retry_product['goodsCode']
                                        success_count += 1
                                        
                                        # Update or create EFRISGood
                                        efris_good = db.query(EFRISGood).filter(
                                            EFRISGood.company_id == company_id,
                                            EFRISGood.goods_code == retry_product['goodsCode']
                                        ).first()
                                        
                                        if efris_good:
                                            # Update existing
                                            efris_good.goods_name = retry_product['goodsName']
                                            efris_good.unit_price = float(retry_product['unitPrice'])
                                        else:
                                            # Create new
                                            efris_good = EFRISGood(
                                                company_id=company_id,
                                                goods_code=retry_product['goodsCode'],
                                                goods_name=retry_product['goodsName'],
                                                commodity_category_code=retry_product['commodityCategoryId'],
                                                commodity_category_name="",
                                                unit_price=float(retry_product['unitPrice']),
                                                currency="UGX",
                                                tax_rate=0.18,
                                                have_excise_tax=retry_product['haveExciseTax'],
                                                stock=0,
                                                efris_data=retry_item_result
                                            )
                                            db.add(efris_good)
                                        
                                        # Remove from failed items if it was added
                                        failed_items = [f for f in failed_items if f.get('name') != product.qb_name]
                                    else:
                                        failed_items.append({
                                            "name": product.qb_name,
                                            "error": f"Retry failed: {retry_msg or 'Unknown error'}"
                                        })
                else:
                    # Retry itself failed
                    print(f"[Register Items] Retry failed with code: {retry_result.get('returnStateInfo', {}).get('returnCode')}")
                    for retry_idx, (orig_idx, product, retry_product) in enumerate(items_to_retry):
                        if not any(f.get('name') == product.qb_name for f in failed_items):
                            failed_items.append({
                                "name": product.qb_name,
                                "error": f"Retry failed: {retry_result.get('returnStateInfo', {}).get('returnMessage', 'Unknown error')}"
                            })
            
            # After successful registration, add opening stock for items that have QtyOnHand > 0
            # EFRIS requires T131 (Stock Increase) to set initial stock, not T130
            # NOTE: Product model doesn't have qb_qty_on_hand field - would need to fetch from QB if needed
            items_with_opening_stock = []
            # Commenting out for now - opening stock would need to be set separately via T131
            # for idx, product in enumerate(products):
            #     if product.efris_status == "Registered":
            #         items_with_opening_stock.append({
            #             "product": product,
            #             "goodsCode": efris_products[idx]['goodsCode'],
            #             "quantity": 0,  # Would need to get from QuickBooks
            #             "unitPrice": product.qb_unit_price or 0
            #         })
            
            if items_with_opening_stock:
                print(f"[Register Items] Adding opening stock for {len(items_with_opening_stock)} items via T131")
                try:
                    # Prepare T131 stock increase request
                    stock_data = {
                        "goodsStockIn": {
                            "operationType": "101",  # Stock increase
                            "supplierTin": company.tin or "",
                            "supplierName": company.name or "Opening Stock",
                            "remarks": "Opening stock - Initial inventory",
                            "stockInDate": datetime.now().strftime("%Y-%m-%d"),
                            "stockInType": "101",  # 101=Opening Stock
                            "productionBatchNo": "",
                            "productionDate": ""
                        },
                        "goodsStockInItem": [
                            {
                                "goodsCode": item["goodsCode"],
                                "quantity": item["quantity"],
                                "unitPrice": item["unitPrice"]
                            }
                            for item in items_with_opening_stock
                        ]
                    }
                    
                    stock_result = manager.stock_increase(stock_data)
                    print(f"[Register Items] Opening stock result: {json.dumps(stock_result, indent=2)[:500]}")
                    
                    # Update stock in EFRISGood table
                    if stock_result.get('returnStateInfo', {}).get('returnCode') == '00':
                        for item in items_with_opening_stock:
                            efris_good = db.query(EFRISGood).filter(
                                EFRISGood.company_id == company_id,
                                EFRISGood.goods_code == item["goodsCode"]
                            ).first()
                            if efris_good:
                                efris_good.stock = item["quantity"]
                        print(f"[Register Items] Successfully added opening stock for {len(items_with_opening_stock)} items")
                except Exception as stock_err:
                    print(f"[Register Items] Warning: Failed to add opening stock: {stock_err}")
                    # Don't fail the entire registration if opening stock fails
            
            db.commit()
        else:
            # Entire batch failed
            error_msg = result.get('returnStateInfo', {}).get('returnMessage', 'Unknown error')
            print(f"[Register Items] Batch failed: {error_msg}")
            failed_items = [{"name": p.qb_name, "error": error_msg} for p in products]
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
            "message": f"Successfully registered {success_count} out of {len(products)} items to EFRIS",
            "efris_response": result
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] Registration failed with exception:\n{error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/qb-invoices/import")
async def import_qb_invoices_to_db(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch QB invoices and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Fetch from QuickBooks
        invoices = qb_client.get_invoices(max_results=1000)
        
        saved_count = 0
        for inv in invoices:
            # Parse transaction date
            txn_date = None
            if inv.get('TxnDate'):
                try:
                    txn_date = datetime.strptime(inv.get('TxnDate'), '%Y-%m-%d')
                except:
                    pass
            
            # Check if already exists
            existing = db.query(Invoice).filter(
                Invoice.company_id == company_id,
                Invoice.qb_invoice_id == inv.get('Id')
            ).first()
            
            if existing:
                # Update existing
                existing.qb_doc_number = inv.get('DocNumber')
                existing.qb_customer_name = inv.get('CustomerRef', {}).get('name')
                existing.qb_txn_date = txn_date
                existing.qb_total_amt = float(inv.get('TotalAmt', 0))
                existing.qb_data = inv
                existing.updated_at = datetime.now()
            else:
                # Create new
                invoice = Invoice(
                    company_id=company_id,
                    qb_invoice_id=inv.get('Id'),
                    qb_doc_number=inv.get('DocNumber'),
                    qb_customer_name=inv.get('CustomerRef', {}).get('name'),
                    qb_txn_date=txn_date,
                    qb_total_amt=float(inv.get('TotalAmt', 0)),
                    qb_data=inv,
                    efris_status='Pending'
                )
                db.add(invoice)
                saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {len(invoices)} invoices ({saved_count} new, {len(invoices)-saved_count} updated)",
            "count": len(invoices)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/companies/{company_id}/qb-invoices/sync-efris")
async def sync_qb_invoices_with_efris(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync QB invoices in database with EFRIS fiscalized invoices"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        manager = get_efris_manager(company)
        
        synced_count = 0
        print(f"[SYNC] Querying EFRIS for fiscalized invoices...")
        
        # Query EFRIS for recent invoices
        efris_result = manager.query_invoices({'pageNo': '1', 'pageSize': '100'})
        
        if isinstance(efris_result, dict) and 'data' in efris_result:
            efris_data = efris_result['data'].get('decrypted_content', {})
            efris_records = efris_data.get('records', [])
            print(f"[SYNC] Found {len(efris_records)} EFRIS invoices")
            
            # Match EFRIS invoices with QB invoices by reference number
            for efris_rec in efris_records:
                fdn = efris_rec.get('invoiceNo')
                reference_no = efris_rec.get('referenceNo')  # This is the QB DocNumber
                
                if reference_no:
                    print(f"[SYNC] Checking EFRIS invoice {fdn} with reference {reference_no}")
                    # Find QB invoice by DocNumber
                    qb_inv = db.query(Invoice).filter(
                        Invoice.company_id == company_id,
                        Invoice.qb_doc_number == reference_no
                    ).first()
                    
                    if qb_inv:
                        print(f"[SYNC] Found matching QB invoice {reference_no}")
                        # Check if we have an EFRISInvoice record for this QB invoice
                        efris_inv = db.query(EFRISInvoice).filter(
                            EFRISInvoice.company_id == company_id,
                            EFRISInvoice.qb_invoice_id == qb_inv.qb_invoice_id
                        ).first()
                        
                        # Parse issued date
                        issued_date = None
                        try:
                            if efris_rec.get('issuedDate'):
                                issued_date = datetime.strptime(efris_rec.get('issuedDate'), '%d/%m/%Y %H:%M:%S')
                        except:
                            pass
                        
                        # Convert invoice date
                        invoice_date = qb_inv.qb_txn_date.date() if qb_inv.qb_txn_date else None
                        
                        if not efris_inv:
                            print(f"[SYNC] Creating new EFRIS invoice record for {reference_no}")
                            # Create EFRIS invoice record with fiscalized status
                            efris_inv = EFRISInvoice(
                                company_id=company_id,
                                qb_invoice_id=qb_inv.qb_invoice_id,
                                qb_invoice_number=qb_inv.qb_doc_number,
                                invoice_date=invoice_date,
                                customer_name=qb_inv.qb_customer_name,
                                total_amount=qb_inv.qb_total_amt,
                                status='success',
                                fdn=fdn,
                                invoice_no=fdn,
                                buyer_legal_name=efris_rec.get('buyerLegalName'),
                                buyer_business_name=efris_rec.get('buyerBusinessName'),
                                buyer_tin=efris_rec.get('buyerTin'),
                                currency=efris_rec.get('currency'),
                                gross_amount=float(efris_rec.get('grossAmount', 0)),
                                tax_amount=float(efris_rec.get('taxAmount', 0)),
                                net_amount=float(efris_rec.get('netAmount', 0)) if efris_rec.get('netAmount') else None,
                                issued_date=issued_date,
                                efris_data=efris_rec
                            )
                            db.add(efris_inv)
                            synced_count += 1
                        elif not efris_inv.fdn or efris_inv.status != 'success':
                            print(f"[SYNC] Updating existing EFRIS invoice record for {reference_no}")
                            # Update existing record that doesn't have FDN yet or is not marked as success
                            efris_inv.status = 'success'
                            efris_inv.fdn = fdn
                            efris_inv.invoice_no = fdn
                            efris_inv.error_message = None
                            efris_inv.buyer_legal_name = efris_rec.get('buyerLegalName')
                            efris_inv.buyer_business_name = efris_rec.get('buyerBusinessName')
                            efris_inv.buyer_tin = efris_rec.get('buyerTin')
                            efris_inv.currency = efris_rec.get('currency')
                            efris_inv.gross_amount = float(efris_rec.get('grossAmount', 0))
                            efris_inv.tax_amount = float(efris_rec.get('taxAmount', 0))
                            efris_inv.net_amount = float(efris_rec.get('netAmount', 0)) if efris_rec.get('netAmount') else None
                            efris_inv.issued_date = issued_date
                            efris_inv.efris_data = efris_rec
                            synced_count += 1
            
            if synced_count > 0:
                db.commit()
                print(f"[SYNC] Successfully synced {synced_count} invoices with EFRIS")
            
            return {
                "success": True,
                "message": f"Synced {synced_count} invoices with EFRIS",
                "synced_count": synced_count,
                "efris_count": len(efris_records)
            }
        else:
            return {
                "success": False,
                "message": "Could not retrieve EFRIS invoices",
                "synced_count": 0
            }
            
    except Exception as e:
        print(f"[SYNC] Error syncing with EFRIS: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-invoices")
async def get_saved_qb_invoices(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get QB invoices saved in database with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # First, auto-fix any successful invoices with missing FDN
    fix_missing_fdns(db, company_id)
    
    query = db.query(Invoice).filter(Invoice.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Invoice.qb_doc_number.ilike(search_pattern)) |
            (Invoice.qb_customer_name.ilike(search_pattern))
        )
    
    invoices = query.order_by(Invoice.qb_txn_date.desc()).all()
    
    # Build response with EFRIS status from EFRISInvoice table
    result_invoices = []
    for inv in invoices:
        # Look up EFRIS status from EFRISInvoice table
        efris_inv = db.query(EFRISInvoice).filter(
            EFRISInvoice.company_id == company_id,
            EFRISInvoice.qb_invoice_id == inv.qb_invoice_id
        ).first()
        
        if efris_inv:
            efris_status = efris_inv.status
            efris_fdn = efris_inv.fdn
        else:
            efris_status = 'draft'
            efris_fdn = None
        
        result_invoices.append({
            "Id": inv.qb_invoice_id,
            "DocNumber": inv.qb_doc_number,
            "CustomerRef": {"name": inv.qb_customer_name},
            "TxnDate": inv.qb_txn_date.isoformat() if inv.qb_txn_date else None,
            "TotalAmt": inv.qb_total_amt,
            "EfrisStatus": efris_status,
            "EfrisFDN": efris_fdn
        })
    
    return {
        "count": len(result_invoices),
        "invoices": result_invoices
    }


@app.post("/api/companies/{company_id}/qb-purchase-orders/import")
async def import_qb_pos_to_db(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch QB POs and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Fetch from QuickBooks
        pos = qb_client.get_purchase_orders()
        
        saved_count = 0
        for po in pos:
            # Parse transaction date
            txn_date = None
            if po.get('TxnDate'):
                try:
                    txn_date = datetime.strptime(po.get('TxnDate'), '%Y-%m-%d')
                except:
                    pass
            
            # Check if already exists
            existing = db.query(PurchaseOrder).filter(
                PurchaseOrder.company_id == company_id,
                PurchaseOrder.qb_po_id == po.get('Id')
            ).first()
            
            if existing:
                # Update existing
                existing.qb_doc_number = po.get('DocNumber')
                existing.qb_vendor_name = po.get('VendorRef', {}).get('name')
                existing.qb_txn_date = txn_date
                existing.qb_total_amt = float(po.get('TotalAmt', 0))
                existing.qb_data = po
                existing.updated_at = datetime.now()
            else:
                # Create new
                purchase_order = PurchaseOrder(
                    company_id=company_id,
                    qb_po_id=po.get('Id'),
                    qb_doc_number=po.get('DocNumber'),
                    qb_vendor_name=po.get('VendorRef', {}).get('name'),
                    qb_txn_date=txn_date,
                    qb_total_amt=float(po.get('TotalAmt', 0)),
                    qb_data=po
                )
                db.add(purchase_order)
                saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {len(pos)} purchase orders ({saved_count} new, {len(pos)-saved_count} updated)",
            "count": len(pos)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-purchase-orders")
async def get_saved_qb_pos(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get QB POs saved in database with full details"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == company_id).all()
    
    # Return full details from QuickBooks using the global qb_client
    full_pos = []
    
    for po in pos:
        try:
            full_po = qb_client.get_purchase_order(po.qb_po_id)
            if full_po:
                full_pos.append(full_po)
        except Exception as e:
            # If we can't get full details, return summary
            full_pos.append({
                "Id": po.qb_po_id,
                "DocNumber": po.qb_doc_number,
                "VendorRef": {"name": po.qb_vendor_name},
                "TxnDate": po.qb_txn_date.isoformat() if po.qb_txn_date else None,
                "TotalAmt": po.qb_total_amt
            })
    
    return full_pos


@app.post("/api/companies/{company_id}/qb-purchase-orders/sync-to-efris")
async def sync_purchase_orders_to_efris(
    company_id: int,
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send purchase orders to EFRIS as stock increases (T131)"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    manager = EfrisManager(
        device_no=company.device_no,
        tin=company.tin,
        private_key=company.private_key
    )
    
    # Fetch purchase orders with full details using global qb_client
    po_ids = request.get('po_ids', [])
    if not po_ids:
        raise HTTPException(status_code=400, detail="No purchase order IDs provided")
    
    synced = []
    failed = []
    
    for po_id in po_ids:
        try:
            # Get PO from database
            db_po = db.query(PurchaseOrder).filter(
                PurchaseOrder.company_id == company_id,
                PurchaseOrder.qb_po_id == str(po_id)
            ).first()
            
            if not db_po:
                failed.append({"po_id": po_id, "error": "Not found in database"})
                continue
            
            # Get full PO from QuickBooks
            po = qb_client.get_purchase_order(str(po_id))
            if not po:
                failed.append({"po_id": po_id, "error": "Not found in QuickBooks"})
                continue
            
            # Build stock increase (T131) payload
            items = []
            for line in po.get('Line', []):
                if line.get('DetailType') != 'ItemBasedExpenseLineDetail':
                    continue
                
                detail = line.get('ItemBasedExpenseLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                item_id = item_ref.get('value')
                
                if not item_id:
                    continue
                
                # Get product from database
                product = db.query(Product).filter(
                    Product.company_id == company_id,
                    Product.qb_product_id == item_id
                ).first()
                
                if not product or not product.efris_goodsCode:
                    failed.append({
                        "po_id": po_id,
                        "item": item_ref.get('name'),
                        "error": "Product not registered in EFRIS"
                    })
                    continue
                
                qty = float(detail.get('Qty', 0))
                unit_price = float(detail.get('UnitPrice', 0))
                
                items.append({
                    "commodityGoodsId": "",
                    "goodsCode": product.efris_goodsCode,
                    "measureUnit": product.efris_unit or "101",
                    "quantity": str(qty),
                    "unitPrice": str(unit_price),
                    "remarks": f"PO {po.get('DocNumber')}"
                })
            
            if not items:
                failed.append({"po_id": po_id, "error": "No valid items to sync"})
                continue
            
            # Send to EFRIS
            stock_data = {
                "goodsStockIn": {
                    "operationType": "101",  # Opening stock
                    "supplierTin": "",
                    "supplierName": po.get('VendorRef', {}).get('name', 'Vendor'),
                    "adjustType": "",
                    "remarks": f"Purchase Order {po.get('DocNumber')}",
                    "stockInDate": po.get('TxnDate', datetime.now().strftime("%Y-%m-%d")),
                    "stockInType": "102",  # Purchase
                    "productionBatchNo": "",
                    "productionDate": "",
                    "branchId": "",
                    "invoiceNo": po.get('DocNumber', ''),
                    "isCheckBatchNo": "0",
                    "rollBackIfError": "0"
                },
                "goodsStockInItem": items
            }
            
            result = manager.stock_increase(stock_data)
            
            if result.get('status') == 200:
                synced.append({
                    "po_id": po_id,
                    "doc_number": po.get('DocNumber'),
                    "items": len(items)
                })
            else:
                failed.append({
                    "po_id": po_id,
                    "error": result.get('msg', 'Unknown error')
                })
        
        except Exception as e:
            failed.append({
                "po_id": po_id,
                "error": str(e)
            })
    
    return {
        "synced_count": len(synced),
        "failed_count": len(failed),
        "synced": synced,
        "failed": failed
    }


@app.post("/api/companies/{company_id}/qb-credit-memos/import")
async def import_qb_credit_memos_to_db(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch QB credit memos and save to database"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Fetch from QuickBooks
        credit_memos = qb_client.get_credit_memos(max_results=1000)
        
        saved_count = 0
        for cm in credit_memos:
            # Parse transaction date
            txn_date = None
            if cm.get('TxnDate'):
                try:
                    txn_date = datetime.strptime(cm.get('TxnDate'), '%Y-%m-%d')
                except:
                    pass
            
            # Check if already exists
            existing = db.query(CreditMemo).filter(
                CreditMemo.company_id == company_id,
                CreditMemo.qb_credit_memo_id == cm.get('Id')
            ).first()
            
            if existing:
                # Update existing
                existing.qb_doc_number = cm.get('DocNumber')
                existing.qb_customer_name = cm.get('CustomerRef', {}).get('name')
                existing.qb_txn_date = txn_date
                existing.qb_total_amt = float(cm.get('TotalAmt', 0))
                existing.qb_data = cm
                existing.updated_at = datetime.now()
            else:
                # Create new
                credit_memo = CreditMemo(
                    company_id=company_id,
                    qb_credit_memo_id=cm.get('Id'),
                    qb_doc_number=cm.get('DocNumber'),
                    qb_customer_name=cm.get('CustomerRef', {}).get('name'),
                    qb_txn_date=txn_date,
                    qb_total_amt=float(cm.get('TotalAmt', 0)),
                    qb_data=cm
                )
                db.add(credit_memo)
                saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Imported {len(credit_memos)} credit memos ({saved_count} new, {len(credit_memos)-saved_count} updated)",
            "count": len(credit_memos)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}/qb-credit-memos")
async def get_saved_qb_credit_memos(
    company_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get QB credit memos saved in database with optional search"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(CreditMemo).filter(CreditMemo.company_id == company_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CreditMemo.qb_doc_number.ilike(search_pattern)) |
            (CreditMemo.qb_customer_name.ilike(search_pattern))
        )
    
    credit_memos = query.order_by(CreditMemo.updated_at.desc()).all()
    
    return {
        "count": len(credit_memos),
        "credit_memos": [{
            "Id": cm.qb_credit_memo_id,
            "DocNumber": cm.qb_doc_number,
            "CustomerRef": {"name": cm.qb_customer_name},
            "TxnDate": cm.qb_txn_date.isoformat() if cm.qb_txn_date else None,
            "TotalAmt": cm.qb_total_amt
        } for cm in credit_memos]
    }


# ========== HEALTH CHECK ==========

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

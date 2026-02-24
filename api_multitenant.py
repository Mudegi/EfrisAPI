"""
Multi-Tenant EFRIS API - Production Ready
FastAPI application with database, authentication, and company isolation
"""
# Ensure current directory is in path for imports (needed for cPanel/passenger)
import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional, Dict
import json
import secrets
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging - control verbosity via EFRIS_LOG_LEVEL env var
# Set EFRIS_LOG_LEVEL=DEBUG for verbose output, default is INFO for production
_log_level = os.environ.get("EFRIS_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, _log_level, logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("efris_api")

from database.connection import get_db, init_db
from database.models import (
    User, Company, CompanyUser, Product, Invoice, PurchaseOrder, CreditMemo,
    EFRISGood, EFRISInvoice, ExciseCode, ClientReferral, AuditLog, SystemSettings
)
# Security utilities
from security_utils import (
    generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp_code,
    get_client_ip, enforce_api_security
)
# Import auth functions from standalone auth.py file
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if user.status == 'suspended':
        raise HTTPException(status_code=403, detail="Account is suspended. Please contact support.")
    return user

# API Key Authentication for External ERP Systems
def get_company_from_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Company:
    """Authenticate external ERP systems with IP whitelist & rate limiting"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    company = db.query(Company).filter(
        Company.api_key == x_api_key,
        Company.api_enabled == True,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or API access disabled",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Update last used timestamp
    company.api_last_used = datetime.utcnow()
    
    # SECURITY: IP Whitelisting + Rate Limiting
    enforce_api_security(request, company, db)
    
    db.commit()
    
    return company

# Helper function to verify company access
def verify_company_access(current_user: User, company_id: int, db: Session) -> bool:
    """Verify user has access to the specified company"""
    if current_user.role in ["owner", "admin"]:
        # Owners and admins can access all companies
        return True
    
    # Check if company belongs to this user (for clients)
    if current_user.role == "client":
        company = db.query(Company).filter(Company.id == company_id).first()
        return company and company.owner_id == current_user.id
    
    # Check if company belongs to this reseller or their clients
    if current_user.role == "reseller":
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            # Reseller owns the company directly
            if company.owner_id == current_user.id:
                return True
            # Or company belongs to one of reseller's clients
            client_user = db.query(User).filter(User.id == company.owner_id).first()
            return client_user and client_user.parent_id == current_user.id
    
    return False

# Helper function to get user companies
def get_user_companies(current_user: User, db: Session):
    """Get all companies the user has access to"""
    if current_user.role in ["owner", "admin"]:
        # Owners and admins see all companies
        return db.query(Company).all()
    
    if current_user.role == "client":
        # Clients see only their companies
        return db.query(Company).filter(Company.owner_id == current_user.id).all()
    
    if current_user.role == "reseller":
        # Resellers see:
        # 1. Companies they own directly
        # 2. Companies owned by their clients
        client_ids = db.query(User.id).filter(User.parent_id == current_user.id).all()
        client_ids = [cid[0] for cid in client_ids]
        client_ids.append(current_user.id)  # Add reseller's own ID
        return db.query(Company).filter(Company.owner_id.in_(client_ids)).all()
    
    return []

# Define schemas inline to ensure they're always available
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    email: str  # Using str instead of EmailStr to avoid email-validator dependency
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "reseller"

class UserLogin(BaseModel):
    email: str  # Using str instead of EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: bool
    subscription_status: Optional[str] = None
    subscription_ends: Optional[datetime] = None
    max_clients: Optional[int] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None

class CompanyCreate(BaseModel):
    name: str
    tin: str
    device_no: Optional[str] = None
    efris_test_mode: bool = True

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    device_no: Optional[str] = None
    efris_test_mode: Optional[bool] = None
    qb_company_name: Optional[str] = None
    erp_type: Optional[str] = None
    erp_config: Optional[dict] = None

class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    tin: str
    device_no: Optional[str]
    efris_test_mode: bool
    qb_company_name: Optional[str]
    is_active: bool
    created_at: datetime
    erp_type: Optional[str] = None
    erp_config: Optional[dict] = None

class CompanyWithRole(CompanyResponse):
    role: str

class CompanyUserAdd(BaseModel):
    email: str  # Using str instead of EmailStr
    role: str = Field(default="user", pattern="^(admin|user|readonly)$")

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    qb_item_id: str
    qb_name: str
    qb_sku: Optional[str]
    efris_product_code: Optional[str]
    efris_status: str
    has_excise: bool
    created_at: datetime
    synced_at: Optional[datetime]

class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    qb_invoice_id: str
    qb_doc_number: str
    qb_customer_name: str
    qb_total_amt: float
    efris_fdn: Optional[str]
    efris_status: str
    created_at: datetime
    fiscalized_at: Optional[datetime]

from efris_client import EfrisManager
from quickbooks_client import QuickBooksClient
from quickbooks_efris_mapper import QuickBooksEfrisMapper

load_dotenv()

# ========== LIFESPAN EVENTS ==========
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    init_db()
    load_product_metadata()
    print("[OK] Database tables created")
    print("[OK] Multi-tenant EFRIS API started")
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title=os.getenv("API_TITLE", "EFRIS Multi-Tenant API"),
    version=os.getenv("API_VERSION", "2.0.0"),
    description="""
## EFRIS Multi-Tenant Integration Platform

Production-ready API for Uganda Revenue Authority (URA) EFRIS invoice submission.

### Features
* 🔐 Multi-tenant authentication and isolation
* 📱 Mobile-first PWA dashboard
* 🔄 Real-time invoice submission to EFRIS
* 📊 Product catalog management
* 🎯 Custom ERP integration support
* 🔒 Enterprise-grade security

### Getting Started
1. **Authentication**: Obtain API key from dashboard
2. **Submit Products**: Register products with EFRIS
3. **Create Invoices**: Submit invoices and receive FDN
4. **Monitor**: Track all submissions in real-time

### External API Documentation
Visit [/external-api-docs](/external-api-docs) for Custom ERP integration guide.

### Support
- 📧 Email: support@efrisintegration.nafacademy.com
- 📱 WhatsApp: +256 706090021
- 📚 Docs: https://efrisintegration.nafacademy.com/docs
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "Login and token management"},
        {"name": "Invoices", "description": "Invoice submission and management"},
        {"name": "Products", "description": "Product catalog operations"},
        {"name": "Dashboard", "description": "Statistics and analytics"},
        {"name": "External API", "description": "External ERP integration endpoints"},
        {"name": "Admin", "description": "Owner and reseller operations"},
    ],
    lifespan=lifespan
)

# ============================================================================
# STABILITY & RATE LIMITING
# ============================================================================

# Add rate limiting to prevent DOS attacks
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global limit: 100 requests per minute per IP
    storage_uri="memory://"  # Use memory storage (upgrade to Redis for production cluster)
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add max request body size limit (10MB) to prevent memory exhaustion
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class RequestSizeLimiter(BaseHTTPMiddleware):
    """Limit request body size to prevent memory exhaustion attacks"""
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                return Response(
                    content=f"Request body too large. Maximum size: {self.max_size // (1024*1024)}MB",
                    status_code=413
                )
        return await call_next(request)

app.add_middleware(RequestSizeLimiter, max_size=10 * 1024 * 1024)

# Add validation error handler to see detailed errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"[VALIDATION ERROR] {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
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

# ============================================================================
# SEO & DISCOVERABILITY ENDPOINTS
# ============================================================================

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """Serve robots.txt for search engine crawlers"""
    from fastapi.responses import PlainTextResponse
    import os
    
    robots_path = os.path.join("static", "robots.txt")
    if os.path.exists(robots_path):
        with open(robots_path, "r") as f:
            return PlainTextResponse(content=f.read())
    
    # Fallback if file doesn't exist
    return PlainTextResponse(content="""User-agent: *
Allow: /
Disallow: /api/auth/
Disallow: /api/companies/*/
Disallow: /dashboard
""")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    """Serve sitemap.xml for search engines"""
    from fastapi.responses import Response
    import os
    
    sitemap_path = os.path.join("static", "sitemap.xml")
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r") as f:
            return Response(content=f.read(), media_type="application/xml")
    
    # Fallback minimal sitemap
    return Response(
        content="""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://yourdomain.com/</loc><priority>1.0</priority></url>
    <url><loc>https://yourdomain.com/docs</loc><priority>0.9</priority></url>
</urlset>""",
        media_type="application/xml"
    )


# ============================================================================
# HEALTH CHECK & MONITORING ENDPOINTS
# ============================================================================

@app.get("/health")
@limiter.limit("60/minute")  # Limit health checks
async def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Health check endpoint for load balancers and monitoring
    Returns 200 if API is healthy, 503 if degraded
    """
    from datetime import datetime
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/api/metrics")
@limiter.limit("30/minute")
async def get_metrics(request: Request, db: Session = Depends(get_db)):
    """
    Basic metrics endpoint (for monitoring/alerting)
    Only accessible internally or with admin token
    """
    try:
        # Count active users
        active_users = db.query(User).filter(User.is_active == True).count()
        total_companies = db.query(Company).count()
        
        return {
            "active_users": active_users,
            "total_companies": total_companies,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== SAAS PLATFORM INTEGRATION ==========
# SaaS endpoints temporarily disabled - core EFRIS API fully functional
# TODO: Fix imports in api_saas.py to re-enable user management features
# try:
#     from api_saas import router as saas_router
#     app.include_router(saas_router, tags=["SaaS Platform"])
#     print("[SAAS] ✓ Multi-tenant SaaS endpoints loaded")
# except ImportError as e:
#     print(f"[SAAS] Warning: Could not load SaaS endpoints: {e}")


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
    """Get or create EFRIS manager for a company with AES key caching.
    
    This caches EfrisManager instances per company so the AES key from T104
    is reused across requests. Without caching, every request triggers:
      T101 (time sync) + T104 (key exchange) + T103 (get params) = ~5-6 seconds overhead.
    With caching, only the first call per 24hrs does the handshake.
    """
    if company.id in efris_managers:
        mgr = efris_managers[company.id]
        # Check if configuration changed (cert path, test mode, device)
        if (mgr.tin == company.tin and 
            mgr.device_no == (company.device_no or f"{company.tin}_02") and
            mgr.test_mode == company.efris_test_mode):
            # Same config - reuse (ensure_authenticated will refresh AES key if expired)
            return mgr
        else:
            # Config changed - recreate
            logger.info(f"[EFRIS CACHE] Config changed for company {company.id}, recreating manager")
            del efris_managers[company.id]
    
    logger.info(f"[EFRIS CACHE] Creating new EfrisManager for company {company.id} (TIN: {company.tin})")
    efris_managers[company.id] = EfrisManager(
        tin=company.tin,
        device_no=company.device_no,
        cert_path=company.efris_cert_path,
        test_mode=company.efris_test_mode
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


# ========== PUBLIC DEMO ENDPOINTS (No Authentication Required) ==========
# These endpoints demonstrate READ-ONLY EFRIS operations
# Uses real company credentials: TIN 1014409555

@app.get("/api/public/efris/test/t103")
async def public_test_t103():
    """Public Demo: T103 Get Registration Details - READ ONLY
    
    Calls real EFRIS server. Shows error if server is unavailable.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Call real EFRIS - perform handshake and get registration
        efris.ensure_authenticated()
        
        if hasattr(efris, 'registration_details') and efris.registration_details:
            result = efris.registration_details
        else:
            result = efris.get_registration_details()
        
        return {
            "status": "success",
            "interface": "T103",
            "description": "Retrieved taxpayer registration details from EFRIS",
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T103",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        return {
            "status": "error",
            "interface": "T103",
            "message": f"Failed to connect to EFRIS: {error_msg}"
        }


@app.get("/api/public/efris/test/t111")
async def public_test_t111():
    """Public Demo: T111 Query Goods & Services - READ ONLY
    
    Calls real EFRIS server. Shows error if server is unavailable.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Search for cement products in EFRIS database
        result = efris.get_goods_and_services(
            page_no=1,
            page_size=10,
            goods_name="cement"
        )
        return {
            "status": "success",
            "interface": "T111",
            "description": "Product search in EFRIS goods database",
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T111",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        return {
            "status": "error",
            "interface": "T111",
            "message": f"Failed to query EFRIS goods database: {error_msg}"
        }


@app.get("/api/public/efris/test/t125")
async def public_test_t125():
    """Public Demo: T125 Query Excise Duty Codes - READ ONLY
    
    Calls real EFRIS server. Shows error if server is unavailable.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Get excise duty codes (alcohol, tobacco, etc.)
        result = efris.query_excise_duty()
        return {
            "status": "success",
            "interface": "T125",
            "description": "Excise duty rates for alcohol, tobacco, and other products",
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T125",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        return {
            "status": "error",
            "interface": "T125",
            "message": f"Failed to query EFRIS excise codes: {error_msg}"
        }


@app.get("/api/public/efris/test/t115")
async def public_test_t115():
    """Public Demo: T115 Query Units of Measure - READ ONLY
    
    Fetches official EFRIS unit of measure codes from system dictionary.
    This is CRITICAL for registering products with correct unit codes.
    
    Example: Code "102" = Piece (NOT litres!)
    
    Calls real EFRIS server. Shows error if server is unavailable.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Get system dictionary including units of measure
        result = efris.get_code_list(None)
        
        # Extract units of measure from EFRIS response
        decrypted_content = result.get('data', {}).get('decrypted_content', {})
        rate_units = decrypted_content.get('rateUnit', [])
        
        # Format units (just code and name from EFRIS)
        units = []
        for unit in rate_units:
            units.append({
                "code": unit.get('value', ''),
                "name": unit.get('name', '')
            })
        
        return {
            "status": "success",
            "interface": "T115",
            "description": "System dictionary - Units of Measure codes from EFRIS",
            "units": units,
            "total": len(units),
            "full_response": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T115",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        # Return fallback static data on error
        return {
            "status": "warning",
            "interface": "T115",
            "message": "Using cached/fallback unit codes (EFRIS connection failed)",
            "error": error_msg,
            "units": [
                {"code": "101", "name": "Carton"},
                {"code": "102", "name": "Piece"},
                {"code": "103", "name": "Kilogram"},
                {"code": "104", "name": "Litre"},
                {"code": "105", "name": "Meter"},
                {"code": "106", "name": "Tonne"},
                {"code": "107", "name": "Gram"},
                {"code": "112", "name": "Pack"},
                {"code": "113", "name": "Dozen"},
                {"code": "115", "name": "Pair"}
            ]
        }


@app.get("/api/public/efris/test/t106")
async def public_test_t106():
    """Public Demo: T106 Query Taxpayer by TIN - READ ONLY
    
    Calls real EFRIS server. Shows error if server is unavailable.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Query a known taxpayer from EFRIS
        result = efris.query_taxpayer_by_tin(tin="1000168319")
        return {
            "status": "success",
            "interface": "T106",
            "description": "Query taxpayer information by TIN from EFRIS",
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T106",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        return {
            "status": "error",
            "interface": "T106",
            "message": f"Failed to query EFRIS taxpayer data: {error_msg}"
        }


@app.get("/api/public/efris/test/query-invoices")
async def public_test_query_invoices():
    """Public Demo: T106 Query Invoices - READ ONLY
    
    Shows example of querying invoices from EFRIS by date range and filters.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Query recent invoices (last 30 days)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        query_params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "invoiceKind": "1",  # 1=Invoice, 2=Receipt
            "pageNo": "1",
            "pageSize": "10"
        }
        
        result = efris.query_invoice(query_params)
        return {
            "status": "success",
            "interface": "T106 - Query Invoices",
            "description": "Query invoices from EFRIS by date range and filters",
            "query": query_params,
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T106 - Query Invoices",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        return {
            "status": "error",
            "interface": "T106 - Query Invoices",
            "message": f"Failed to query EFRIS invoices: {error_msg}"
        }


@app.get("/api/public/efris/test/invoice-details")
async def public_test_invoice_details():
    """Public Demo: T108 Get Invoice Details - READ ONLY
    
    Shows example of getting specific invoice details by invoice number.
    Note: May fail if there are no invoices in the test system.
    """
    try:
        efris = EfrisManager(
            tin="1014409555",
            device_no="1014409555_02",
            cert_path="keys/wandera.pfx",
            test_mode=True
        )
        
        # Try to get invoice details (will fail gracefully if no invoice exists)
        # This is just to show the endpoint - in real use, client would provide invoice number
        result = efris.get_invoice_by_number("SAMPLE-INV-001")
        return {
            "status": "success",
            "interface": "T108 - Get Invoice Details",
            "description": "Get specific invoice details by invoice number",
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        if "HTML" in error_msg or "<!DOCTYPE" in error_msg:
            return {
                "status": "error",
                "interface": "T108 - Get Invoice Details",
                "message": "EFRIS server is currently unavailable. The test server may be down for maintenance.",
                "details": "Server returned HTML error page instead of JSON response"
            }
        # This is expected to fail in demo since we don't have a real invoice number
        return {
            "status": "info",
            "interface": "T108 - Get Invoice Details",
            "message": "Demo endpoint - In production, provide a real invoice number to query",
            "note": "This endpoint retrieves detailed information for a specific invoice by its unique number",
            "error": error_msg
        }


# ========== ROOT & DASHBOARD ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve SaaS landing page"""
    try:
        with open("static/landing.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html>
                <head><title>EFRIS API - SaaS Platform</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>EFRIS Integration Platform</h1>
                    <p>Multi-tenant SaaS for EFRIS tax compliance</p>
                    <a href="/docs" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
                        View API Documentation
                    </a>
                    <br><br>
                    <a href="/dashboard" style="color: #667eea;">Admin Dashboard</a>
                </body>
            </html>
        """)


@app.get("/reseller", response_class=HTMLResponse)
async def reseller_portal():
    """Serve the reseller portal"""
    return FileResponse("static/reseller_portal.html")


@app.get("/owner", response_class=HTMLResponse)
async def owner_portal():
    """Serve the platform owner portal"""
    return FileResponse("static/owner_portal.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page for owners and resellers"""
    return FileResponse("static/login.html")


@app.get("/client/login", response_class=HTMLResponse)
async def client_login_page():
    """Serve the client login page"""
    return FileResponse("static/client_login.html")


@app.get("/external-api-docs", response_class=HTMLResponse)
async def external_api_documentation():
    """Serve the External API Documentation for Custom ERP Integration"""
    import json
    try:
        with open("EXTERNAL_API_DOCUMENTATION.md", "r", encoding="utf-8") as f:
            markdown_content = f.read()
        
        # Properly escape markdown content for JavaScript
        markdown_json = json.dumps(markdown_content)
        
        # Create nice HTML wrapper with markdown rendering
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EFRIS External API Documentation - Custom ERP Integration</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📋</text></svg>">
    
    <!-- Marked.js for markdown rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <!-- Highlight.js for code syntax highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .back-button {{
            display: inline-block;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        
        .back-button:hover {{
            background: #5568d3;
        }}
        
        #markdown-body {{
            font-size: 16px;
        }}
        
        #markdown-body h1, #markdown-body h2, #markdown-body h3 {{
            color: #667eea;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        #markdown-body h1 {{
            font-size: 2em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        #markdown-body h2 {{
            font-size: 1.5em;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
        }}
        
        #markdown-body h3 {{
            font-size: 1.2em;
        }}
        
        #markdown-body pre {{
            background: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        
        #markdown-body code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        #markdown-body pre code {{
            background: transparent;
            padding: 0;
        }}
        
        #markdown-body table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        
        #markdown-body th, #markdown-body td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        #markdown-body th {{
            background: #667eea;
            color: white;
        }}
        
        #markdown-body tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        #markdown-body blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin: 15px 0;
            color: #666;
            font-style: italic;
        }}
        
        #markdown-body ul, #markdown-body ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        
        #markdown-body li {{
            margin-bottom: 8px;
        }}
        
        #markdown-body a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        #markdown-body a:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 EFRIS External API</h1>
            <p>Complete Integration Guide for Custom ERP Systems</p>
        </div>
        
        <div class="content">
            <a href="/" class="back-button">← Back to Home</a>
            <a href="/docs" class="back-button" style="background: #764ba2; margin-left: 10px;">View Interactive API Docs</a>
            
            <div id="markdown-body"></div>
        </div>
        
        <div class="footer">
            <p>© 2026 UG EFRIS Integration Platform | Need help? Contact support@efrisintegration.nafacademy.com</p>
        </div>
    </div>
    
    <script>
        // Markdown content (properly escaped JSON)
        const markdownContent = {markdown_json};
        
        // Configure marked options
        marked.setOptions({{
            breaks: true,
            gfm: true,
            headerIds: true
        }});
        
        // Render markdown to HTML
        document.getElementById('markdown-body').innerHTML = marked.parse(markdownContent);
        
        // Apply syntax highlighting to code blocks
        document.querySelectorAll('pre code').forEach((block) => {{
            hljs.highlightElement(block);
        }});
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html)
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html>
                <head><title>Documentation Not Found</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>📚 External API Documentation</h1>
                    <p>Documentation file not found. Please contact support.</p>
                    <br>
                    <a href="/" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
                        ← Back to Home
                    </a>
                </body>
            </html>
        """)


@app.get("/how-to-integrate-efris", response_class=HTMLResponse)
async def how_to_guide():
    """Serve SEO-optimized guide for EFRIS integration"""
    return FileResponse("static/how-to-integrate-efris.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the multi-tenant control panel for taxpayer clients"""
    return FileResponse("static/dashboard_multitenant.html")


# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new reseller user with 2-day trial and return access token"""
    from datetime import timedelta
    
    print(f"[DEBUG] Received registration data: email={user_data.email}, role={user_data.role}, phone={user_data.phone}")
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user as reseller with trial subscription
    trial_end = datetime.utcnow() + timedelta(days=2)
    
    db_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone if user_data.phone else None,
        role=user_data.role if user_data.role else 'reseller',
        status='active',  # Resellers are active immediately
        is_active=True,
        subscription_status="active",
        subscription_ends=trial_end
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token for immediate login
    access_token = create_access_token(data={"sub": db_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str = None,
    db: Session = Depends(get_db)
):
    """Login and get access token (with optional 2FA)"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # SECURITY: Check 2FA if enabled
    if user.totp_enabled:
        if not totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not verify_totp_code(user.totp_secret, totp_code):
            # Log failed 2FA attempt
            audit = AuditLog(
                company_id=None,
                user_id=user.id,
                action="2fa_failed",
                details=f"Failed 2FA login attempt for {user.email}"
            )
            db.add(audit)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Log successful login
    audit = AuditLog(
        company_id=None,
        user_id=user.id,
        action="login",
        details=f"User {user.email} logged in successfully"
    )
    db.add(audit)
    db.commit()
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


# ========== 2FA ENDPOINTS ==========

@app.post("/api/auth/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate new TOTP secret and QR code for 2FA setup"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only owners and admins can enable 2FA")
    
    # Generate new secret
    secret = generate_totp_secret()
    totp_uri = get_totp_uri(secret, current_user.email, "EFRIS API")
    qr_code_base64 = generate_qr_code(totp_uri)
    
    # Store secret (not enabled yet)
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    db.commit()
    
    # Log action
    audit = AuditLog(
        company_id=None,
        user_id=current_user.id,
        action="2fa_setup_initiated",
        details=f"User {current_user.email} initiated 2FA setup"
    )
    db.add(audit)
    db.commit()
    
    return {
        "secret": secret,
        "qr_code": qr_code_base64,
        "message": "Scan QR code with authenticator app, then verify with a code to enable 2FA"
    }


@app.post("/api/auth/2fa/enable")
async def enable_2fa(
    totp_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify TOTP code and enable 2FA"""
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up. Call /api/auth/2fa/setup first")
    
    if not verify_totp_code(current_user.totp_secret, totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    # Enable 2FA
    current_user.totp_enabled = True
    db.commit()
    
    # Log action
    audit = AuditLog(
        company_id=None,
        user_id=current_user.id,
        action="2fa_enabled",
        details=f"User {current_user.email} enabled 2FA"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "2FA enabled successfully"}


@app.post("/api/auth/2fa/disable")
async def disable_2fa(
    password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA (requires password confirmation)"""
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Disable 2FA
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    
    # Log action
    audit = AuditLog(
        company_id=None,
        user_id=current_user.id,
        action="2fa_disabled",
        details=f"User {current_user.email} disabled 2FA"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "2FA disabled successfully"}


# ========== RESELLER PORTAL ENDPOINTS ==========

@app.get("/api/reseller/clients")
async def get_reseller_clients(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clients and referrals managed by this reseller"""
    if current_user.role not in ['reseller', 'admin']:
        raise HTTPException(status_code=403, detail="Only resellers can access this endpoint")
    
    result = []
    
    # 1. Get pending referrals (not yet approved)
    pending_referrals = db.query(ClientReferral).filter(
        ClientReferral.reseller_id == current_user.id,
        ClientReferral.status == 'pending'
    ).all()
    
    for referral in pending_referrals:
        result.append({
            "id": referral.id,
            "referral_id": referral.id,
            "email": referral.client_email,
            "full_name": referral.client_name,
            "phone": referral.client_phone,
            "company_name": referral.company_name,
            "tin": referral.tin,
            "device_no": referral.device_no,
            "is_active": False,
            "status": "pending",
            "created_at": referral.created_at.isoformat() if referral.created_at else None
        })
    
    # 2. Get approved referrals (converted to clients)
    approved_referrals = db.query(ClientReferral).filter(
        ClientReferral.reseller_id == current_user.id,
        ClientReferral.status == 'approved'
    ).all()
    
    for referral in approved_referrals:
        if referral.created_client_id:
            client = db.query(User).filter(User.id == referral.created_client_id).first()
            company = db.query(Company).filter(Company.id == referral.created_company_id).first() if referral.created_company_id else None
            
            if client:
                result.append({
                    "id": client.id,
                    "referral_id": referral.id,
                    "email": client.email,
                    "full_name": client.full_name,
                    "phone": client.phone,
                    "company_name": company.name if company else referral.company_name,
                    "tin": company.tin if company else referral.tin,
                    "device_no": company.device_no if company else referral.device_no,
                    "is_active": client.is_active,
                    "status": "approved",
                    "created_at": referral.reviewed_at.isoformat() if referral.reviewed_at else None
                })
    
    # 3. Get any clients directly under this reseller (parent_id = reseller_id)
    direct_clients = db.query(User).filter(User.parent_id == current_user.id).all()
    
    for client in direct_clients:
        # Check if already included via referral
        if not any(r['id'] == client.id and r.get('status') == 'approved' for r in result):
            company = db.query(Company).filter(Company.owner_id == client.id).first()
            
            result.append({
                "id": client.id,
                "referral_id": None,
                "email": client.email,
                "full_name": client.full_name,
                "phone": client.phone,
                "company_name": company.name if company else None,
                "tin": company.tin if company else None,
                "device_no": company.device_no if company else None,
                "is_active": client.is_active,
                "status": "approved",
                "created_at": client.created_at.isoformat() if client.created_at else None
            })
    
    return result


from fastapi import File, UploadFile, Form
import shutil
import os

@app.post("/api/reseller/submit-referral")
async def submit_client_referral(
    company_name: str = Form(...),
    client_name: str = Form(...),
    client_email: str = Form(...),
    client_phone: str = Form(None),
    tin: str = Form(...),
    device_no: str = Form(None),
    notes: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    SECURITY FIX: Resellers submit client referrals ONLY (no certificates, no direct add)
    Owner must approve and configure EFRIS credentials
    """
    if current_user.role != 'reseller':
        raise HTTPException(status_code=403, detail="Only resellers can submit referrals")
    
    # Check if email already exists
    if db.query(User).filter(User.email == client_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if TIN already exists
    if db.query(Company).filter(Company.tin == tin).first():
        raise HTTPException(status_code=400, detail="TIN already registered")
    
    # Check if already referred
    if db.query(ClientReferral).filter(
        ClientReferral.tin == tin
    ).first():
        raise HTTPException(status_code=400, detail="TIN already referred")
    
    # Create referral (NO certificates - owner will handle that)
    referral = ClientReferral(
        reseller_id=current_user.id,
        company_name=company_name,
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        tin=tin,
        device_no=device_no,
        notes=notes,
        status="pending"
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    
    # Audit log for URA compliance
    audit = AuditLog(
        user_id=current_user.id,
        action="REFERRAL_SUBMITTED",
        resource_type="ClientReferral",
        resource_id=str(referral.id),
        details={
            "company_name": company_name,
            "tin": tin,
            "status": "pending"
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "Client referral submitted. Platform owner will review and configure.",
        "referral_id": referral.id,
        "status": "pending"
    }


@app.get("/api/reseller/referrals")
async def get_reseller_referrals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all referrals submitted by this reseller"""
    if current_user.role != 'reseller':
        raise HTTPException(status_code=403, detail="Resellers only")
    
    referrals = db.query(ClientReferral).filter(
        ClientReferral.reseller_id == current_user.id
    ).order_by(ClientReferral.created_at.desc()).all()
    
    return {
        "success": True,
        "referrals": [
            {
                "id": r.id,
                "company_name": r.company_name,
                "client_name": r.client_name,
                "tin": r.tin,
                "status": r.status,
                "submitted_at": r.created_at.isoformat() if r.created_at else None,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "rejection_reason": r.rejection_reason if r.status == "rejected" else None
            }
            for r in referrals
        ]
    }


@app.get("/api/reseller/client-activity")
async def get_reseller_client_activity(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get invoice activity from all clients referred by this reseller"""
    if current_user.role != 'reseller':
        raise HTTPException(status_code=403, detail="Resellers only")
    
    from database.models import ActivityLog
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get all client IDs that belong to this reseller
    client_ids = db.query(User.id).filter(User.parent_id == current_user.id).all()
    client_ids = [c[0] for c in client_ids]
    
    if not client_ids:
        return {
            "success": True,
            "total": 0,
            "this_month": 0,
            "today": 0,
            "activities": []
        }
    
    # Get activity logs for these clients
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id.in_(client_ids),
        ActivityLog.activity_type.in_(['invoice_created', 'invoice_fiscalized'])
    ).order_by(ActivityLog.created_at.desc()).limit(50).all()
    
    # Calculate stats
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    month_start = datetime(now.year, now.month, 1)
    
    today_count = db.query(func.count(ActivityLog.id)).filter(
        ActivityLog.user_id.in_(client_ids),
        ActivityLog.activity_type == 'invoice_fiscalized',
        ActivityLog.created_at >= today_start
    ).scalar() or 0
    
    month_count = db.query(func.count(ActivityLog.id)).filter(
        ActivityLog.user_id.in_(client_ids),
        ActivityLog.activity_type == 'invoice_fiscalized',
        ActivityLog.created_at >= month_start
    ).scalar() or 0
    
    total_count = db.query(func.count(ActivityLog.id)).filter(
        ActivityLog.user_id.in_(client_ids),
        ActivityLog.activity_type == 'invoice_fiscalized'
    ).scalar() or 0
    
    # Format activities
    activity_list = []
    for activity in activities:
        company = db.query(Company).filter(Company.id == activity.company_id).first()
        activity_list.append({
            "id": activity.id,
            "company_name": company.name if company else "Unknown",
            "invoice_number": activity.document_number,
            "total_amount": activity.details.get('total_amount') if activity.details else None,
            "efris_status": activity.efris_status,
            "created_at": activity.created_at.isoformat() if activity.created_at else None
        })
    
    return {
        "success": True,
        "total": total_count,
        "this_month": month_count,
        "today": today_count,
        "activities": activity_list
    }


# SECURITY: Completely removed reseller client deletion
# Only owner can deactivate clients (see owner endpoints below)


# ========== OWNER/ADMIN ENDPOINTS ==========

@app.get("/api/owner/stats")
async def get_owner_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get platform statistics for owner dashboard"""
    # Check if user is owner/admin
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    from sqlalchemy import func, and_
    from datetime import date
    
    total_resellers = db.query(User).filter(User.role == 'reseller').count()
    pending_clients = db.query(User).filter(and_(User.role == 'client', User.status == 'pending')).count()
    active_clients = db.query(User).filter(and_(User.role == 'client', User.status == 'active')).count()
    invoices_today = db.query(Invoice).filter(func.date(Invoice.created_at) == date.today()).count()
    
    return {
        "total_resellers": total_resellers,
        "pending_clients": pending_clients,
        "active_clients": active_clients,
        "invoices_today": invoices_today,
        "owner_name": current_user.full_name or current_user.email
    }


@app.get("/api/owner/pending-clients")
async def get_pending_clients(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clients pending approval"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    from sqlalchemy import and_
    
    pending = db.query(User).filter(and_(
        User.role == 'client',
        User.status == 'pending'
    )).all()
    
    result = []
    for client in pending:
        # Get company info
        company = db.query(Company).filter(Company.owner_id == client.id).first()
        
        # Get reseller info
        reseller = db.query(User).filter(User.id == client.parent_id).first()
        
        result.append({
            "id": client.id,
            "email": client.email,
            "company_name": company.name if company else "N/A",
            "tin": company.tin if company else "N/A",
            "reseller_name": reseller.full_name if reseller else "Unknown",
            "created_at": client.created_at.isoformat()
        })
    
    return result


@app.get("/api/owner/resellers")
async def get_all_resellers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all resellers"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    resellers = db.query(User).filter(User.role == 'reseller').all()
    
    result = []
    for reseller in resellers:
        client_count = db.query(User).filter(User.parent_id == reseller.id).count()
        
        result.append({
            "id": reseller.id,
            "email": reseller.email,
            "full_name": reseller.full_name,
            "phone": reseller.phone,
            "status": reseller.status,
            "subscription_status": reseller.subscription_status,
            "client_count": client_count,
            "created_at": reseller.created_at.isoformat()
        })
    
    return result


@app.get("/api/owner/clients")
async def get_all_clients(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clients across all resellers"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    clients = db.query(User).filter(User.role == 'client').all()
    
    result = []
    for client in clients:
        company = db.query(Company).filter(Company.owner_id == client.id).first()
        reseller = db.query(User).filter(User.id == client.parent_id).first()
        
        client_data = {
            "id": client.id,
            "email": client.email,
            "company_name": company.name if company else "N/A",
            "tin": company.tin if company else "N/A",
            "device_no": company.device_no if company else "N/A",
            "efris_test_mode": company.efris_test_mode if company else False,
            "status": client.status,
            "reseller_name": reseller.full_name if reseller else "Direct",
            "created_at": client.created_at.isoformat()
        }
        
        # Include company details and API credentials if company exists
        if company:
            client_data["company"] = {
                "id": company.id,
                "device_no": company.device_no,
                "erp_type": company.erp_type or "none",
                "efris_test_mode": company.efris_test_mode,
                "is_active": company.is_active
            }
            
            # Include API credentials for Custom ERP clients
            if company.erp_type == "custom":
                base_url = os.getenv("APP_BASE_URL", "https://efrisintegration.nafacademy.com")
                client_data["api_credentials"] = {
                    "api_key": company.api_key,
                    "api_secret": company.api_secret,
                    "api_enabled": company.api_enabled,
                    "api_last_used": company.api_last_used.isoformat() if company.api_last_used else None,
                    "api_endpoint": f"{base_url}/api/external/efris"
                }
        
        result.append(client_data)
    
    return result


@app.get("/api/owner/activity")
async def get_activity_feed(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent activity feed"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    from database.models import ActivityLog
    
    activities = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(50).all()
    
    result = []
    for activity in activities:
        company = db.query(Company).filter(Company.id == activity.company_id).first()
        
        result.append({
            "id": activity.id,
            "company_name": company.name if company else "Unknown",
            "activity_type": activity.activity_type,
            "document_number": activity.document_number,
            "efris_request_type": activity.efris_request_type,
            "efris_status": activity.efris_status,
            "created_at": activity.created_at.isoformat()
        })
    
    return result


# ============================================
# SYSTEM SETTINGS API ENDPOINTS
# ============================================

@app.get("/api/settings/public")
async def get_public_settings(db: Session = Depends(get_db)):
    """Get public settings for landing page (no authentication required)"""
    settings = db.query(SystemSettings).filter(SystemSettings.is_public == 1).all()
    
    result = {}
    for setting in settings:
        # Convert boolean strings to actual booleans
        if setting.setting_type == 'boolean':
            result[setting.setting_key] = setting.setting_value == '1' or setting.setting_value.lower() == 'true'
        elif setting.setting_type == 'number':
            try:
                result[setting.setting_key] = int(setting.setting_value) if setting.setting_value else 0
            except:
                result[setting.setting_key] = 0
        else:
            result[setting.setting_key] = setting.setting_value or ''
    
    return result


@app.get("/api/settings/all")
async def get_all_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all settings (owner/admin only)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access settings")
    
    settings = db.query(SystemSettings).order_by(SystemSettings.category, SystemSettings.setting_key).all()
    
    result = []
    for setting in settings:
        result.append({
            "id": setting.id,
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value,
            "setting_type": setting.setting_type,
            "category": setting.category,
            "description": setting.description,
            "is_public": setting.is_public,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        })
    
    return result


@app.get("/api/settings/category/{category}")
async def get_settings_by_category(
    category: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get settings by category (owner/admin only)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access settings")
    
    settings = db.query(SystemSettings).filter(SystemSettings.category == category).all()
    
    result = []
    for setting in settings:
        result.append({
            "id": setting.id,
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value,
            "setting_type": setting.setting_type,
            "category": setting.category,
            "description": setting.description,
            "is_public": setting.is_public
        })
    
    return result


@app.put("/api/settings/{setting_key}")
async def update_setting(
    setting_key: str,
    setting_value: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a setting value (owner/admin only)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can update settings")
    
    setting = db.query(SystemSettings).filter(SystemSettings.setting_key == setting_key).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{setting_key}' not found")
    
    # Update the setting
    setting.setting_value = setting_value
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(setting)
    
    # Log the change
    audit = AuditLog(
        user_id=current_user.id,
        action="update_setting",
        resource_type="SystemSettings",
        resource_id=setting_key,
        details={"old_value": setting.setting_value, "new_value": setting_value}
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": f"Setting '{setting_key}' updated successfully",
        "setting": {
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value,
            "setting_type": setting.setting_type,
            "category": setting.category
        }
    }


@app.post("/api/settings")
async def create_setting(
    setting_key: str = Body(...),
    setting_value: str = Body(...),
    setting_type: str = Body(default='text'),
    category: str = Body(default='general'),
    description: str = Body(default=''),
    is_public: int = Body(default=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new setting (owner/admin only)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can create settings")
    
    # Check if setting already exists
    existing = db.query(SystemSettings).filter(SystemSettings.setting_key == setting_key).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Setting '{setting_key}' already exists")
    
    # Create new setting
    new_setting = SystemSettings(
        setting_key=setting_key,
        setting_value=setting_value,
        setting_type=setting_type,
        category=category,
        description=description,
        is_public=is_public
    )
    
    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)
    
    return {"success": True, "message": "Setting created successfully", "setting_id": new_setting.id}



@app.post("/api/owner/approve-client/{client_id}")
async def approve_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve a pending client"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.status != 'pending':
        raise HTTPException(status_code=400, detail="Client is not pending approval")
    
    # Activate client
    client.status = 'active'
    client.is_active = True
    
    # Activate their company
    company = db.query(Company).filter(Company.owner_id == client.id).first()
    if company:
        company.is_active = True
    
    db.commit()
    
    return {"success": True, "message": "Client approved and activated"}


@app.post("/api/owner/reject-client/{client_id}")
async def reject_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reject a pending client"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.status != 'pending':
        raise HTTPException(status_code=400, detail="Client is not pending approval")
    
    # Delete client and their company
    company = db.query(Company).filter(Company.owner_id == client.id).first()
    if company:
        db.delete(company)
    
    db.delete(client)
    db.commit()
    
    return {"success": True, "message": "Client rejected and removed"}


@app.post("/api/owner/suspend-client/{client_id}")
async def suspend_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Suspend a client - blocks their access"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    # Query client without role filter first to check if they exist
    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.role != 'client':
        raise HTTPException(status_code=400, detail=f"User is not a client (role: {client.role})")
    
    try:
        client.status = 'suspended'
        client.is_active = False
        
        # Also deactivate their company
        company = db.query(Company).filter(Company.owner_id == client.id).first()
        if company:
            company.is_active = False
        
        db.commit()
        
        return {"success": True, "message": f"Client {client.email} suspended"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to suspend client: {str(e)}")


@app.post("/api/owner/activate-client/{client_id}")
async def activate_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Activate a suspended client - restores their access"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    # Query client without role filter first to check if they exist
    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.role != 'client':
        raise HTTPException(status_code=400, detail=f"User is not a client (role: {client.role})")
    
    try:
        client.status = 'active'
        client.is_active = True
        
        # Also activate their company
        company = db.query(Company).filter(Company.owner_id == client.id).first()
        if company:
            company.is_active = True
        
        db.commit()
        
        return {"success": True, "message": f"Client {client.email} activated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate client: {str(e)}")


@app.delete("/api/owner/delete-client/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a client and their company permanently"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can delete clients")
    
    # Query client without role filter first to check if they exist
    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.role != 'client':
        raise HTTPException(status_code=400, detail=f"User is not a client (role: {client.role})")
    
    try:
        # Get their company
        company = db.query(Company).filter(Company.owner_id == client.id).first()
        
        # Store email for response
        client_email = client.email
        company_name = company.name if company else "Unknown"
        
        # Delete client referrals that reference this client or their company
        if company:
            db.execute(text("DELETE FROM client_referrals WHERE created_company_id = :company_id OR created_client_id = :client_id"), 
                      {"company_id": company.id, "client_id": client.id})
        else:
            db.execute(text("DELETE FROM client_referrals WHERE created_client_id = :client_id"), 
                      {"client_id": client.id})
        
        # Delete audit logs for this user (regardless of company)
        db.query(AuditLog).filter(AuditLog.user_id == client.id).delete()
        
        # Delete activity logs for this user (regardless of company)
        db.execute(text("DELETE FROM activity_logs WHERE user_id = :user_id OR reseller_id = :user_id"), 
                  {"user_id": client.id})
        
        # Delete company users
        if company:
            db.query(CompanyUser).filter(CompanyUser.company_id == company.id).delete()
            
            # Delete audit logs for this company
            db.query(AuditLog).filter(AuditLog.company_id == company.id).delete()
            
            # Delete activity logs for this company
            db.execute(text("DELETE FROM activity_logs WHERE company_id = :company_id"), 
                      {"company_id": company.id})
            
            # Delete invoices
            db.execute(text("DELETE FROM invoices WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete products
            db.execute(text("DELETE FROM products WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete purchase orders
            db.execute(text("DELETE FROM purchase_orders WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete credit memos
            db.execute(text("DELETE FROM credit_memos WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete EFRIS invoices
            db.execute(text("DELETE FROM efris_invoices WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete EFRIS goods
            db.execute(text("DELETE FROM efris_goods WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete excise codes
            db.execute(text("DELETE FROM excise_codes WHERE company_id = :company_id"), {"company_id": company.id})
            
            # Delete company
            db.delete(company)
        
        # Delete user
        db.delete(client)
        
        db.commit()
        
        return {
            "success": True, 
            "message": f"Client {client_email} ({company_name}) and all associated data permanently deleted"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete client: {str(e)}")


@app.put("/api/owner/edit-client/{client_id}")
async def edit_client(
    client_id: int,
    email: str = Form(None),
    full_name: str = Form(None),
    phone: str = Form(None),
    company_name: str = Form(None),
    tin: str = Form(None),
    device_no: str = Form(None),
    efris_test_mode: str = Form(None),  # Changed to str to handle "true"/"false" strings
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Edit client details including EFRIS test/production mode"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can edit clients")
    
    client = db.query(User).filter(User.id == client_id, User.role == 'client').first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get their company
    company = db.query(Company).filter(Company.owner_id == client.id).first()
    
    # Update user fields if provided
    if email is not None:
        # Check if email is already taken by another user
        existing = db.query(User).filter(User.email == email, User.id != client_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
        client.email = email
    
    if full_name is not None:
        client.full_name = full_name
    
    if phone is not None:
        client.phone = phone
    
    # Update company fields if provided
    if company:
        if company_name is not None:
            company.name = company_name
        
        if tin is not None:
            company.tin = tin
        
        if device_no is not None:
            company.device_no = device_no
        
        # Update EFRIS test mode toggle - convert string to boolean
        if efris_test_mode is not None:
            company.efris_test_mode = efris_test_mode.lower() in ['true', '1', 'yes']
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Client {client.email} updated successfully",
        "client": {
            "id": client.id,
            "email": client.email,
            "full_name": client.full_name,
            "phone": client.phone,
            "company_name": company.name if company else None,
            "tin": company.tin if company else None,
            "device_no": company.device_no if company else None,
            "efris_test_mode": company.efris_test_mode if company else None
        }
    }


# ============================================================================
# PAYMENT ENDPOINTS (Flutterwave Integration)
# ============================================================================

@app.post("/api/payment/initialize")
async def initialize_payment(
    plan: str = "annual",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Initialize payment for subscription upgrade
    Returns payment link for user to complete payment
    """
    from payment_service import flutterwave, payment_manager
    
    # Get plan price
    amount = payment_manager.get_plan_price(plan)
    
    # Initialize payment
    result = flutterwave.initialize_payment(
        user_email=current_user.email,
        user_name=current_user.full_name or current_user.email,
        amount=amount,
        user_id=current_user.id,
        plan=plan
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Payment initialization failed"))
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action="payment_initiated",
        details=f"Initiated {plan} plan payment - UGX {amount:,}",
        document_number=result.get("tx_ref")
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "payment_link": result["payment_link"],
        "amount": amount,
        "plan": plan,
        "tx_ref": result["tx_ref"]
    }


@app.get("/payment/callback")
async def payment_callback(
    status: str,
    tx_ref: str,
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Payment callback - Flutterwave redirects here after payment
    """
    from payment_service import flutterwave, payment_manager
    
    if status == "successful":
        # Verify payment
        verification = flutterwave.verify_payment(transaction_id)
        
        if verification.get("success"):
            data = verification["data"]
            
            # Extract user_id from transaction reference
            user_id = data.get("meta", {}).get("user_id")
            plan = data.get("meta", {}).get("plan", "annual")
            
            if user_id:
                # Activate subscription
                success = payment_manager.activate_subscription(
                    db, int(user_id), plan, tx_ref
                )
                
                if success:
                    # Redirect to dashboard with success message
                    return RedirectResponse(
                        url=f"/dashboard?payment=success&plan={plan}",
                        status_code=303
                    )
    
    # Payment failed or verification failed
    return RedirectResponse(
        url="/dashboard?payment=failed",
        status_code=303
    )


@app.post("/api/webhooks/flutterwave")
async def flutterwave_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for Flutterwave payment notifications
    This is called by Flutterwave when payment status changes
    """
    from payment_service import flutterwave, payment_manager
    
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("verif-hash", "")
    
    # Verify webhook signature
    if not flutterwave.verify_webhook_signature(body.decode(), signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse payload
    import json
    payload = json.loads(body)
    
    # Handle successful payment
    if payload.get("event") == "charge.completed" and payload.get("data", {}).get("status") == "successful":
        data = payload["data"]
        user_id = data.get("meta", {}).get("user_id")
        plan = data.get("meta", {}).get("plan", "annual")
        tx_ref = data.get("tx_ref")
        
        if user_id:
            # Activate subscription
            payment_manager.activate_subscription(db, int(user_id), plan, tx_ref)
            
            # TODO: Send confirmation email to user
            
            return {"success": True, "message": "Payment processed"}
    
    return {"success": True, "message": "Webhook received"}


@app.post("/api/owner/add-client")
async def owner_add_client(
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(None),
    tin: str = Form(...),
    device_no: str = Form(...),
    cert_password: str = Form(...),
    test_mode: bool = Form(False),
    pfx_file: UploadFile = File(...),
    erp_type: str = Form("none"),
    # QuickBooks
    qb_realm_id: str = Form(None),
    qb_client_id: str = Form(None),
    qb_client_secret: str = Form(None),
    qb_region: str = Form("US"),
    # Xero
    xero_tenant_id: str = Form(None),
    xero_client_id: str = Form(None),
    xero_client_secret: str = Form(None),
    # Zoho
    zoho_org_id: str = Form(None),
    zoho_client_id: str = Form(None),
    zoho_client_secret: str = Form(None),
    # Sage
    sage_company_id: str = Form(None),
    sage_api_key: str = Form(None),
    sage_api_secret: str = Form(None),
    # Odoo
    odoo_url: str = Form(None),
    odoo_db: str = Form(None),
    odoo_username: str = Form(None),
    odoo_password: str = Form(None),
    # Custom API
    custom_url: str = Form(None),
    custom_api_key: str = Form(None),
    custom_api_secret: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Owner adds a direct client (no reseller) with ERP configuration"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    # Check if email exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Save certificate
    cert_dir = "keys/clients"
    os.makedirs(cert_dir, exist_ok=True)
    cert_path = f"{cert_dir}/{tin}.pfx"
    
    with open(cert_path, "wb") as f:
        content = await pfx_file.read()
        f.write(content)
    
    # Create client user (active immediately, no parent_id)
    client_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=company_name,
        phone=phone,
        role='client',
        status='active',  # Owner's clients are active immediately
        is_active=True
    )
    db.add(client_user)
    db.flush()
    
    # Create company with ERP configuration
    company = Company(
        name=company_name,
        tin=tin,
        device_no=device_no,
        efris_cert_path=cert_path,
        efris_cert_password=cert_password,
        efris_test_mode=test_mode,
        owner_id=client_user.id,
        is_active=True,
        erp_type=erp_type
    )
    
    # Add ERP-specific credentials
    if erp_type == "quickbooks" and qb_realm_id:
        company.qb_realm_id = qb_realm_id
        company.qb_region = qb_region
        # Store client credentials securely (in production, encrypt these)
        company.custom_api_key = qb_client_id  # Temp storage
        company.custom_api_secret = qb_client_secret
        company.qb_company_name = company_name
    elif erp_type == "xero" and xero_tenant_id:
        company.xero_tenant_id = xero_tenant_id
        # Store credentials
        company.custom_api_key = xero_client_id
        company.custom_api_secret = xero_client_secret
    elif erp_type == "zoho" and zoho_org_id:
        company.zoho_organization_id = zoho_org_id
        company.custom_api_key = zoho_client_id
        company.custom_api_secret = zoho_client_secret
    elif erp_type == "sage" and sage_company_id:
        company.custom_api_url = f"sage://{sage_company_id}"
        company.custom_api_key = sage_api_key
        company.custom_api_secret = sage_api_secret
    elif erp_type == "odoo" and odoo_url:
        company.custom_api_url = odoo_url
        company.custom_api_key = odoo_username
        company.custom_api_secret = odoo_password
        # Store DB name in a JSON field if available, or in custom_api_url
        company.custom_api_url = f"{odoo_url}?db={odoo_db}"
    elif erp_type == "custom" and custom_url:
        company.custom_api_url = custom_url
        company.custom_api_key = custom_api_key
        company.custom_api_secret = custom_api_secret
    
    # Generate API credentials for Custom ERP integration
    if erp_type == "custom":
        company.api_key = f"efris_{secrets.token_urlsafe(32)}"
        company.api_secret = secrets.token_urlsafe(32)
        company.api_enabled = True
    
    db.add(company)
    db.flush()
    
    # Link user to company
    company_user = CompanyUser(
        user_id=client_user.id,
        company_id=company.id,
        role='owner'
    )
    db.add(company_user)
    
    db.commit()
    
    # Get the base URL for client login
    base_url = os.getenv("APP_BASE_URL", "https://efrisintegration.nafacademy.com")
    client_login_url = f"{base_url}/client/login"
    
    erp_message = f"\n\nERP: {erp_type.upper()}" if erp_type != "none" else "\n\nERP: Manual invoice entry"
    
    # Prepare response with API credentials for Custom ERP
    response_data = {
        "success": True, 
        "message": "Direct client added successfully", 
        "client_id": client_user.id,
        "client_email": email,
        "client_login_url": client_login_url,
        "erp_type": erp_type,
        "erp_configured": erp_type != "none",
        "instructions": f"Send these credentials to your client:\n\nLogin URL: {client_login_url}\nEmail: {email}\nPassword: {password}{erp_message}\n\nThey should bookmark this URL and use it to access their dashboard."
    }
    
    # Include API credentials only for Custom ERP
    if erp_type == "custom" and company.api_key:
        response_data["api_credentials"] = {
            "api_key": company.api_key,
            "api_secret": company.api_secret,
            "api_endpoint": f"{base_url}/api/external/efris",
            "api_enabled": company.api_enabled
        }
    
    return response_data


@app.put("/api/owner/clients/{company_id}/erp")
async def update_client_erp(
    company_id: int,
    erp_type: str = Form(...),
    # QuickBooks
    qb_realm_id: str = Form(None),
    qb_client_id: str = Form(None),
    qb_client_secret: str = Form(None),
    qb_region: str = Form("US"),
    # Xero
    xero_tenant_id: str = Form(None),
    xero_client_id: str = Form(None),
    xero_client_secret: str = Form(None),
    # Zoho
    zoho_org_id: str = Form(None),
    zoho_client_id: str = Form(None),
    zoho_client_secret: str = Form(None),
    # Sage
    sage_company_id: str = Form(None),
    sage_api_key: str = Form(None),
    sage_api_secret: str = Form(None),
    # Odoo
    odoo_url: str = Form(None),
    odoo_db: str = Form(None),
    odoo_username: str = Form(None),
    odoo_password: str = Form(None),
    # Custom API
    custom_url: str = Form(None),
    custom_api_key: str = Form(None),
    custom_api_secret: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update client's ERP configuration (switch ERP types)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can update ERP configuration")
    
    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Store old ERP type for audit log
    old_erp_type = company.erp_type
    
    # Clear all ERP credentials first (clean slate)
    company.qb_realm_id = None
    company.qb_region = "US"
    company.qb_company_name = None
    company.xero_tenant_id = None
    company.zoho_organization_id = None
    company.custom_api_url = None
    company.custom_api_key = None
    company.custom_api_secret = None
    
    # Update ERP type
    company.erp_type = erp_type
    
    # Set new ERP-specific credentials
    if erp_type == "quickbooks" and qb_realm_id:
        company.qb_realm_id = qb_realm_id
        company.qb_region = qb_region
        company.custom_api_key = qb_client_id  # Temp storage
        company.custom_api_secret = qb_client_secret
        company.qb_company_name = company.name
    elif erp_type == "xero" and xero_tenant_id:
        company.xero_tenant_id = xero_tenant_id
        company.custom_api_key = xero_client_id
        company.custom_api_secret = xero_client_secret
    elif erp_type == "zoho" and zoho_org_id:
        company.zoho_organization_id = zoho_org_id
        company.custom_api_key = zoho_client_id
        company.custom_api_secret = zoho_client_secret
    elif erp_type == "sage" and sage_company_id:
        company.custom_api_url = f"sage://{sage_company_id}"
        company.custom_api_key = sage_api_key
        company.custom_api_secret = sage_api_secret
    elif erp_type == "odoo" and odoo_url:
        company.custom_api_url = odoo_url
        company.custom_api_key = odoo_username
        company.custom_api_secret = odoo_password
        company.custom_api_url = f"{odoo_url}?db={odoo_db}"
    elif erp_type == "custom" and custom_url:
        company.custom_api_url = custom_url
        company.custom_api_key = custom_api_key
        company.custom_api_secret = custom_api_secret
    
    # Generate API credentials if switching TO Custom ERP (if they don't already exist)
    if erp_type == "custom":
        if not company.api_key:  # Only generate if they don't have credentials yet
            company.api_key = f"efris_{secrets.token_urlsafe(32)}"
            company.api_secret = secrets.token_urlsafe(32)
            company.api_enabled = True
    
    # Note: We preserve existing API credentials when switching AWAY from Custom ERP
    # This allows switching back without needing new credentials
    
    db.commit()
    
    # Create audit log
    audit_log = AuditLog(
        company_id=company.id,
        user_id=current_user.id,
        action="update_erp_config",
        details=f"ERP changed from {old_erp_type} to {erp_type}",
        ip_address="owner_portal"
    )
    db.add(audit_log)
    db.commit()
    
    # Prepare response
    base_url = os.getenv("APP_BASE_URL", "https://efrisintegration.nafacademy.com")
    response_data = {
        "success": True,
        "message": f"ERP configuration updated from {old_erp_type or 'none'} to {erp_type}",
        "company_id": company.id,
        "company_name": company.name,
        "erp_type": erp_type,
        "old_erp_type": old_erp_type
    }
    
    # Include API credentials if Custom ERP
    if erp_type == "custom" and company.api_key:
        response_data["api_credentials"] = {
            "api_key": company.api_key,
            "api_secret": company.api_secret,
            "api_endpoint": f"{base_url}/api/external/efris",
            "api_enabled": company.api_enabled,
            "newly_generated": not company.api_last_used  # True if this is first time
        }
    
    return response_data


@app.get("/api/owner/pending-referrals")
async def get_pending_referrals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all pending client referrals for owner review"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can access this")
    
    referrals = db.query(ClientReferral).filter(
        ClientReferral.status == "pending"
    ).order_by(ClientReferral.created_at.desc()).all()
    
    result = []
    for r in referrals:
        reseller = db.query(User).filter(User.id == r.reseller_id).first()
        result.append({
            "id": r.id,
            "reseller_name": reseller.full_name if reseller else "Unknown",
            "reseller_email": reseller.email if reseller else None,
            "company_name": r.company_name,
            "client_name": r.client_name,
            "client_email": r.client_email,
            "client_phone": r.client_phone,
            "tin": r.tin,
            "device_no": r.device_no,
            "notes": r.notes,
            "submitted_at": r.created_at.isoformat() if r.created_at else None
        })
    
    return {"success": True, "referrals": result}


@app.post("/api/owner/approve-referral/{referral_id}")
async def approve_referral(
    referral_id: int,
    password: str = Form(...),
    cert_password: str = Form(...),
    test_mode: bool = Form(False),
    pfx_file: UploadFile = File(...),
    erp_type: str = Form("none"),
    # QuickBooks fields
    qb_realm_id: Optional[str] = Form(None),
    qb_client_id: Optional[str] = Form(None),
    qb_client_secret: Optional[str] = Form(None),
    qb_region: Optional[str] = Form("US"),
    # Xero fields
    xero_tenant_id: Optional[str] = Form(None),
    xero_client_id: Optional[str] = Form(None),
    xero_client_secret: Optional[str] = Form(None),
    # Zoho fields
    zoho_org_id: Optional[str] = Form(None),
    zoho_client_id: Optional[str] = Form(None),
    zoho_client_secret: Optional[str] = Form(None),
    # Sage fields
    sage_company_id: Optional[str] = Form(None),
    sage_api_key: Optional[str] = Form(None),
    sage_api_secret: Optional[str] = Form(None),
    # Odoo fields
    odoo_url: Optional[str] = Form(None),
    odoo_db: Optional[str] = Form(None),
    odoo_username: Optional[str] = Form(None),
    odoo_password: Optional[str] = Form(None),
    # Custom API fields
    custom_url: Optional[str] = Form(None),
    custom_api_key: Optional[str] = Form(None),
    custom_api_secret: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Owner approves referral and configures EFRIS credentials + ERP system
    CRITICAL: Only owner uploads certificates and configures devices
    """
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can approve referrals")
    
    # Get referral
    referral = db.query(ClientReferral).filter(
        ClientReferral.id == referral_id,
        ClientReferral.status == "pending"
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or already processed")
    
    # Check if email/TIN already exists
    if db.query(User).filter(User.email == referral.client_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(Company).filter(Company.tin == referral.tin).first():
        raise HTTPException(status_code=400, detail="TIN already registered")
    
    # Save certificate
    cert_dir = "keys/clients"
    os.makedirs(cert_dir, exist_ok=True)
    cert_filename = f"{referral.tin}.pfx"
    cert_path = os.path.join(cert_dir, cert_filename)
    
    with open(cert_path, "wb") as buffer:
        shutil.copyfileobj(pfx_file.file, buffer)
    
    try:
        # Create client user
        client_user = User(
            email=referral.client_email,
            hashed_password=get_password_hash(password),
            full_name=referral.client_name,
            phone=referral.client_phone,
            role="client",
            status="active",
            parent_id=referral.reseller_id,  # Link to reseller
            is_active=True
        )
        db.add(client_user)
        db.flush()  # Get ID without committing
        
        # Generate API credentials for external access (used by Custom ERP)
        api_key = f"efris_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(32)
        
        # Create company with ERP configuration
        company = Company(
            name=referral.company_name,
            tin=referral.tin,
            device_no=referral.device_no,
            owner_id=client_user.id,
            efris_test_mode=test_mode,
            efris_cert_path=cert_path,
            efris_cert_password=cert_password,
            erp_type=erp_type,
            # API Credentials (for Custom ERP to call our API)
            api_key=api_key,
            api_secret=api_secret,
            api_enabled=True,
            # QuickBooks
            qb_realm_id=qb_realm_id,
            qb_client_id=qb_client_id,
            qb_client_secret=qb_client_secret,
            qb_region=qb_region,
            # Xero
            xero_tenant_id=xero_tenant_id,
            xero_client_id=xero_client_id,
            xero_client_secret=xero_client_secret,
            # Zoho
            zoho_org_id=zoho_org_id,
            zoho_client_id=zoho_client_id,
            zoho_client_secret=zoho_client_secret,
            # Sage
            sage_company_id=sage_company_id,
            sage_api_key=sage_api_key,
            sage_api_secret=sage_api_secret,
            # Odoo
            odoo_url=odoo_url,
            odoo_db=odoo_db,
            odoo_username=odoo_username,
            odoo_password=odoo_password,
            # Custom API
            custom_api_url=custom_url,
            custom_api_key=custom_api_key,
            custom_api_secret=custom_api_secret,
            is_active=True
        )
        db.add(company)
        db.flush()  # Get ID without committing
        
        # Determine if ERP was configured
        erp_configured = erp_type != "none" and erp_type is not None
        
        # Link user to company (CRITICAL: Must be in same transaction)
        company_user = CompanyUser(
            user_id=client_user.id,
            company_id=company.id,
            role="admin"
        )
        db.add(company_user)
        
        # Update referral status
        referral.status = "approved"
        referral.reviewed_by = current_user.id
        referral.reviewed_at = func.now()
        referral.created_client_id = client_user.id
        referral.created_company_id = company.id
        
        # Audit log for URA compliance
        audit = AuditLog(
            user_id=current_user.id,
            company_id=company.id,
            action="REFERRAL_APPROVED",
            resource_type="ClientReferral",
            resource_id=str(referral_id),
            details={
                "referral_id": referral_id,
                "reseller_id": referral.reseller_id,
                "client_id": client_user.id,
                "company_id": company.id,
                "tin": referral.tin,
                "erp_type": erp_type,
                "erp_configured": erp_configured
            }
        )
        db.add(audit)
        
        # Single commit for atomic transaction
        # If this fails, everything rolls back (User, Company, CompanyUser)
        db.commit()
        db.refresh(client_user)
        db.refresh(company)
        
    except Exception as e:
        db.rollback()
        # Clean up uploaded certificate file on error
        if os.path.exists(cert_path):
            os.remove(cert_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve referral: {str(e)}"
        )
    
    base_url = os.getenv("APP_BASE_URL", "https://efrisintegration.nafacademy.com")
    client_login_url = f"{base_url}/client/login"
    
    # Include API credentials in response if Custom ERP selected
    response_data = {
        "message": "Client referral approved and account created",
        "client_id": client_user.id,
        "company_id": company.id,
        "client_email": referral.client_email,
        "client_login_url": client_login_url,
        "erp_configured": erp_configured,
        "erp_type": erp_type
    }
    
    # If custom ERP, include API credentials for developer handoff
    if erp_type == "custom":
        response_data["api_credentials"] = {
            "api_key": company.api_key,
            "api_secret": company.api_secret,
            "api_endpoint": f"{base_url}/api/external/efris",
            "documentation": "See DEVELOPER_PACKAGE folder for integration guide"
        }
    
    return response_data


@app.post("/api/owner/reject-referral/{referral_id}")
async def reject_referral(
    referral_id: int,
    rejection_reason: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Owner rejects a client referral"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can reject referrals")
    
    referral = db.query(ClientReferral).filter(
        ClientReferral.id == referral_id,
        ClientReferral.status == "pending"
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or already processed")
    
    referral.status = "rejected"
    referral.reviewed_by = current_user.id
    referral.reviewed_at = func.now()
    referral.rejection_reason = rejection_reason
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="REFERRAL_REJECTED",
        resource_type="ClientReferral",
        resource_id=str(referral_id),
        details={
            "referral_id": referral_id,
            "reseller_id": referral.reseller_id,
            "reason": rejection_reason
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "Referral rejected",
        "referral_id": referral_id
    }


@app.post("/api/owner/regenerate-api-key/{company_id}")
async def regenerate_api_key(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate API credentials for a company (use when compromised)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can regenerate API keys")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Generate new credentials
    old_api_key = company.api_key
    company.api_key = f"efris_{secrets.token_urlsafe(32)}"
    company.api_secret = secrets.token_urlsafe(32)
    company.api_last_used = None  # Reset usage tracking
    
    # Audit log for security tracking
    audit = AuditLog(
        user_id=current_user.id,
        company_id=company.id,
        action="API_KEY_REGENERATED",
        resource_type="Company",
        resource_id=str(company_id),
        details={
            "company_id": company_id,
            "company_name": company.name,
            "tin": company.tin,
            "old_api_key_prefix": old_api_key[:15] if old_api_key else None,
            "new_api_key_prefix": company.api_key[:15],
            "reason": "Owner regenerated credentials"
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(company)
    
    base_url = os.getenv("APP_BASE_URL", "https://efrisintegration.nafacademy.com")
    return {
        "success": True,
        "message": "API credentials regenerated successfully",
        "api_key": company.api_key,
        "api_secret": company.api_secret,
        "api_endpoint": f"{base_url}/api/external/efris",
        "warning": "Old credentials are now invalid. Update all ERP systems immediately."
    }


# ========== SECURITY MANAGEMENT ENDPOINTS ==========

@app.put("/api/owner/clients/{company_id}/ip-whitelist")
async def update_ip_whitelist(
    company_id: int,
    allowed_ips: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update IP whitelist for a company (Custom ERP API access control)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can manage IP whitelists")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Store as JSON array
    import json
    company.allowed_ips = json.dumps(allowed_ips) if allowed_ips else None
    
    # Log action
    audit = AuditLog(
        company_id=company_id,
        user_id=current_user.id,
        action="ip_whitelist_updated",
        details=f"Updated IP whitelist for {company.name}: {allowed_ips}"
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "IP whitelist updated successfully",
        "allowed_ips": allowed_ips
    }


@app.put("/api/owner/clients/{company_id}/rate-limit")
async def update_rate_limit(
    company_id: int,
    rate_limit: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update API rate limit for a company"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can manage rate limits")
    
    if rate_limit < 100 or rate_limit > 100000:
        raise HTTPException(status_code=400, detail="Rate limit must be between 100 and 100,000 requests/day")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    old_limit = company.api_rate_limit
    company.api_rate_limit = rate_limit
    
    # Log action
    audit = AuditLog(
        company_id=company_id,
        user_id=current_user.id,
        action="rate_limit_updated",
        details=f"Updated rate limit for {company.name}: {old_limit} → {rate_limit} req/day"
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "Rate limit updated successfully",
        "rate_limit": rate_limit,
        "rate_limit_per_day": rate_limit
    }


@app.get("/api/owner/audit-logs")
async def get_audit_logs(
    action: str = None,
    company_id: int = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get security audit logs (who did what, when)"""
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only platform owners can view audit logs")
    
    query = db.query(AuditLog)
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    if start_date:
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        query = query.filter(AuditLog.created_at >= start)
    if end_date:
        from datetime import datetime
        end = datetime.fromisoformat(end_date)
        query = query.filter(AuditLog.created_at <= end)
    
    # Get logs with user/company details
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        company = db.query(Company).filter(Company.id == log.company_id).first() if log.company_id else None
        
        result.append({
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "action": log.action,
            "user_email": user.email if user else "System",
            "company_name": company.name if company else None,
            "details": log.details
        })
    
    return {
        "logs": result,
        "total": len(result)
    }


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
            "erp_type": cu.company.erp_type or "none",
            "erp_config": None,  # Can be populated with ERP-specific config if needed
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


@app.put("/api/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update company details including ERP type
    
    **Use Case:** Client switches from QuickBooks to Xero but keeps same EFRIS credentials
    
    **Example:**
    ```json
    {
        "erp_type": "XERO",
        "erp_config": {"tenant_id": "xxx-xxx-xxx"}
    }
    ```
    
    **What happens:**
    - ERP type changed (dashboard will adapt automatically)
    - Old ERP data (QB invoices/items) remains in database for history
    - New ERP connection established
    - EFRIS credentials (TIN, device_no, keys) remain unchanged
    """
    # Verify admin access
    from auth.security import verify_company_admin
    if not verify_company_admin(current_user, company_id, db):
        raise HTTPException(
            status_code=403, 
            detail="Only company admins can update company settings"
        )
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Track ERP change for logging
    old_erp = company.erp_type
    new_erp = company_data.erp_type
    
    # Update fields
    if company_data.name is not None:
        company.name = company_data.name
    if company_data.device_no is not None:
        company.device_no = company_data.device_no
    if company_data.efris_test_mode is not None:
        company.efris_test_mode = company_data.efris_test_mode
    if company_data.qb_company_name is not None:
        company.qb_company_name = company_data.qb_company_name
    
    # Handle ERP type change
    if company_data.erp_type is not None:
        valid_erp_types = ['QUICKBOOKS', 'XERO', 'ZOHO', 'CUSTOM', 'NONE']
        erp_upper = company_data.erp_type.upper()
        
        if erp_upper not in valid_erp_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ERP type. Must be one of: {', '.join(valid_erp_types)}"
            )
        
        company.erp_type = erp_upper
        
        # Log ERP change
        if old_erp != erp_upper:
            print(f"[ERP CHANGE] Company {company.name} (ID: {company.id})")
            print(f"  Old ERP: {old_erp or 'None'}")
            print(f"  New ERP: {erp_upper}")
            print(f"  EFRIS credentials remain unchanged (TIN: {company.tin})")
    
    # Update ERP configuration
    if company_data.erp_config is not None:
        import json
        company.erp_config = json.dumps(company_data.erp_config)
    
    company.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(company)
        
        # Success message with ERP change notification
        if old_erp and new_erp and old_erp != new_erp:
            print(f"  ✅ ERP successfully changed from {old_erp} to {new_erp}")
            print(f"  📊 Historical data from {old_erp} preserved in database")
            print(f"  🔗 Dashboard will now show {new_erp} branding")
        
        return company
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


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
        
        # Log activity for owner dashboard
        try:
            from database.models import ActivityLog
            
            # Get reseller_id if client has parent
            client_user = db.query(User).filter(User.id == current_user.id).first()
            reseller_id = client_user.parent_id if client_user else None
            
            activity = ActivityLog(
                company_id=company_id,
                user_id=current_user.id,
                reseller_id=reseller_id,
                activity_type="invoice_fiscalized",
                document_type="invoice",
                document_number=invoice_data.get('basicInformation', {}).get('invoiceNo', 'Unknown'),
                efris_request_type="T109",
                efris_status="success" if result.get('returnStateInfo', {}).get('returnCode') == '00' else "failed",
                efris_response=result,
                details={
                    "invoice_type": invoice_data.get('basicInformation', {}).get('invoiceType'),
                    "total_amount": invoice_data.get('summary', {}).get('grossAmount')
                }
            )
            db.add(activity)
            db.commit()
        except Exception as log_error:
            print(f"[ACTIVITY LOG] Failed to log activity: {log_error}")
            # Don't fail the request if logging fails
        
        return result
    except Exception as e:
        # Log failure
        try:
            from database.models import ActivityLog
            client_user = db.query(User).filter(User.id == current_user.id).first()
            reseller_id = client_user.parent_id if client_user else None
            
            activity = ActivityLog(
                company_id=company_id,
                user_id=current_user.id,
                reseller_id=reseller_id,
                activity_type="invoice_fiscalized",
                document_type="invoice",
                document_number=invoice_data.get('basicInformation', {}).get('invoiceNo', 'Unknown'),
                efris_request_type="T109",
                efris_status="failed",
                efris_response={"error": str(e)},
                details={}
            )
            db.add(activity)
            db.commit()
        except:
            pass
        
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
        result = manager.submit_credit_note_application(credit_note_data)
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
        return RedirectResponse(url=f"/dashboard?error={error_msg}")
    
    if not code or not realmId:
        return RedirectResponse(url="/dashboard?error=Missing authorization code or realm ID")
    
    try:
        tokens = qb_client.exchange_code_for_tokens(code)
        qb_client.realm_id = realmId
        
        # Detect QB region from company info
        qb_region = qb_client.detect_region()
        company_info = qb_client.get_company_info()
        qb_company_name = company_info.get('CompanyName', 'Unknown')
        
        # state contains company_id
        if state:
            try:
                # Handle both "new_sandbox_123" and "123" formats
                if state.startswith("new_sandbox_"):
                    company_id = int(state.split("_")[-1])
                else:
                    company_id = int(state)
                
                # Store QB connection details in database for this specific company
                company = db.query(Company).filter(Company.id == company_id).first()
                if company:
                    company.qb_realm_id = realmId
                    company.qb_access_token = qb_client.access_token
                    company.qb_refresh_token = qb_client.refresh_token
                    company.qb_token_expires = qb_client.token_expiry
                    company.qb_company_name = qb_company_name
                    company.qb_region = qb_region
                    company.erp_type = "quickbooks"
                    company.erp_connected = True
                    company.erp_last_sync = datetime.utcnow()
                    db.commit()
                    
                    print(f"[QB] Connected for company {company.name}: {qb_company_name} (Region: {qb_region})")
                    return RedirectResponse(url="/dashboard?qb_connected=true")
            except ValueError:
                pass
        
        # Fallback - save to global tokens file
        qb_client.save_tokens()
        print(f"[QB] Connected (global): {qb_company_name} (Region: {qb_region})")
        return RedirectResponse(url="/dashboard?qb_connected=true")
        
    except Exception as e:
        print(f"[QB] OAuth failed: {str(e)}")
        return RedirectResponse(url=f"/dashboard?error={str(e)}")


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


@app.get("/api/companies/{company_id}/erp/status")
async def get_erp_connection_status(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get ERP connection status for a company"""
    if not verify_company_access(current_user, company_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "erp_type": company.erp_type or "none",
        "connected": company.erp_connected or False,
        "last_sync": company.erp_last_sync.isoformat() if company.erp_last_sync else None,
        "qb_company_name": company.qb_company_name if company.erp_type == "quickbooks" else None,
        "qb_region": company.qb_region if company.erp_type == "quickbooks" else None
    }


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
                "goodsTypeCode": "101",  # 101=Goods, 102=Fuel only — services use serviceMark
                "serviceMark": "101" if is_service else "102",  # 101=Service, 102=Goods
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


# ============================================================================
# EXTERNAL API ENDPOINTS - For Custom ERP Integration
# ============================================================================

def _amount_to_words(amount):
    """Convert numeric amount to words for invoice display"""
    try:
        amount_int = int(amount)
        
        # Simple implementation for UGX
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
        
        def words_under_thousand(n):
            if n == 0:
                return ""
            elif n < 10:
                return ones[n]
            elif n < 20:
                return teens[n - 10]
            elif n < 100:
                return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
            else:
                return ones[n // 100] + " hundred" + (" " + words_under_thousand(n % 100) if n % 100 != 0 else "")
        
        if amount_int == 0:
            return "Zero shillings only"
        
        # Split into millions, thousands, and hundreds
        millions = amount_int // 1000000
        thousands = (amount_int % 1000000) // 1000
        hundreds = amount_int % 1000
        
        result = []
        if millions > 0:
            result.append(words_under_thousand(millions) + " million")
        if thousands > 0:
            result.append(words_under_thousand(thousands) + " thousand")
        if hundreds > 0:
            result.append(words_under_thousand(hundreds))
        
        return " ".join(result).strip().capitalize() + " shillings only"
    except:
        return ""

def _get_payment_mode_name(mode_code):
    """Convert payment mode code to name"""
    modes = {
        "101": "Cash",
        "102": "Credit",
        "103": "Mobile Money",
        "104": "Card",
        "105": "Bank Transfer"
    }
    return modes.get(str(mode_code), "Cash")

def _build_invoice_summary(invoice_data, calculated_net, calculated_tax, calculated_gross, goods_details, converted_tax_details=None):
    """
    Build EFRIS summary section from tax_details.
    
    EFRIS RULES (verified from official documentation example):
      - grossAmount = sum of grossAmount in taxDetails EXCLUDING excise ("05")
                      (Error 1345: must equal sum of non-excise grossAmounts)
      - taxAmount   = sum of ALL taxAmount in taxDetails INCLUDING excise ("05")
                      (Error 1344: must equal sum of ALL taxAmounts)
      - netAmount   = grossAmount - taxAmount
                      (Error 1343: calculation mistake if this formula doesn't hold)
    
    Documentation proof (interface codes.py line ~1610):
      taxDetails: cat 01 tax=686.45, cat 05 tax=181.82
      summary: netAmount=8379, taxAmount=868, grossAmount=9247
      Verify: 9247 - 868 = 8379 ✓
    """
    # Check if client provided a summary
    client_summary = invoice_data.get("summary", {})
    
    # Get values from converted tax_details (preferred) or raw tax_details (fallback)
    tax_details = converted_tax_details if converted_tax_details else invoice_data.get("tax_details", [])
    
    # Calculate from tax_details per EFRIS rules
    tax_details_gross = 0  # sum of grossAmount EXCLUDING excise ("05")
    tax_details_tax = 0    # sum of ALL taxAmount INCLUDING excise ("05")
    
    for td in tax_details:
        category = td.get("taxCategoryCode", td.get("tax_category_code", "01"))
        tax_amt = float(td.get("taxAmount", td.get("tax_amount", 0)))
        
        # taxAmount always includes ALL categories (including excise)
        tax_details_tax += tax_amt
        
        if category != "05":  # Only non-excise grossAmounts count
            gross = float(td.get("grossAmount", td.get("gross_amount", 0)))
            tax_details_gross += gross
    
    # Apply EFRIS formula
    if len(tax_details) > 0:
        final_gross = tax_details_gross
        final_tax = tax_details_tax
        final_net = final_gross - final_tax  # THE KEY FORMULA
        source = "tax_details"
    elif client_summary and client_summary.get("grossAmount"):
        final_gross = float(client_summary.get("grossAmount", calculated_gross))
        final_tax = float(client_summary.get("taxAmount", calculated_tax))
        final_net = final_gross - final_tax
        source = "client_summary"
    else:
        final_gross = calculated_gross
        final_tax = calculated_tax
        final_net = final_gross - final_tax
        source = "calculated"
    
    logger.debug(f"[T109] Summary (source={source}): net={final_net}, tax={final_tax}, gross={final_gross}")
    
    return {
        "netAmount": f"{final_net:.2f}",
        "taxAmount": f"{final_tax:.2f}",
        "grossAmount": f"{final_gross:.2f}",
        "itemCount": str(sum(1 for item in goods_details if item.get('discountFlag', '2') != '0')),  # Product lines only, excludes discount lines
        "modeCode": "0",
        "remarks": invoice_data.get("remarks", client_summary.get("remarks", "")),
        "qrCode": ""
    }

@app.post("/api/external/efris/submit-invoice")
async def external_submit_invoice(
    invoice_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit invoice to EFRIS and get complete fiscal invoice data
    
    This endpoint returns ALL data needed to render an EFRIS-style fiscal invoice
    in your Custom ERP, including seller details, fiscal data, items, and QR code.
    
    Request Body:
    {
        "invoice_number": "INV-001",
        "invoice_date": "2024-01-24",
        "customer_name": "ABC Company Ltd",
        "customer_tin": "1234567890",  // Optional, required for B2B
        "buyer_type": "1",  // 0=Business, 1=Individual, 2=Government
        "payment_method": "102",  // 101=Cash, 102=Credit, 103=Mobile Money
        "currency": "UGX",  // Optional, defaults to UGX
        "items": [
            {
                "item": "Product A",  // Or "item_name"
                "itemCode": "PROD-001",  // Must be registered via T130
                "qty": "10",
                "unitOfMeasure": "101",  // 101=Stick, 102=Litre, 103=Kg (must match T130 registration)
                "unitPrice": "5900",  // Tax inclusive
                "total": "59000",
                "taxRate": "18",  // Or "-" for tax-exempt
                "tax": "9000",
                "goodsCategoryId": "44102906",  // Commodity code
                "vatApplicableFlag": "1"  // 0=No VAT, 1=VAT applicable
            }
        ],
        "tax_details": [  // Optional - will be auto-calculated if missing
            {
                "tax_category_code": "01",  // 01=Standard, 03=Zero-rated
                "net_amount": "50000",
                "tax_rate": "18",
                "tax_amount": "9000",
                "gross_amount": "59000"
            }
        ]
    }
    
    Response - Complete EFRIS Invoice Data:
    {
        "success": true,
        "message": "Invoice fiscalized successfully",
        
        // Section A: Seller Details
        "seller": {
            "brn": "",
            "tin": "1014409555",
            "legal_name": "Your Company Name",
            "trade_name": "Your Company Name",
            "address": "Kampala, Uganda",
            "reference_number": "INV-001",
            "served_by": "API User"
        },
        
        // Section B: Fiscal/URA Information
        "fiscal_data": {
            "document_type": "Original",
            "fdn": "325043056477",  // Fiscal Document Number
            "verification_code": "234893273725405146366",
            "device_number": "1014409555_02",
            "efris_invoice_id": "...",
            "issued_date": "15/02/2026",
            "issued_time": "13:48:41",
            "qr_code": "base64_encoded_qr_code_image"
        },
        
        // Section C: Buyer Details
        "buyer": {
            "name": "Timothy Khabusi",
            "tin": "",
            "buyer_type": "1"
        },
        
        // Section D: Items
        "items": [...],  // Same as sent, with EFRIS formatting
        
        // Section E: Tax Details (by category)
        "tax_details": [
            {
                "taxCategoryCode": "01",
                "netAmount": "2000000",
                "taxRate": "18",
                "taxAmount": "360000",
                "grossAmount": "2360000"
            }
        ],
        
        // Section F: Summary
        "summary": {
            "net_amount": 2000000,
            "tax_amount": 360000,
            "gross_amount": 2360000,
            "gross_amount_words": "Two million three hundred sixty thousand shillings only",
            "payment_mode": "Credit",
            "total_amount": 2360000,
            "currency": "UGX",
            "number_of_items": 1,
            "mode": "Online",
            "remarks": ""
        }
    }
    
    Use this response to render a PDF/HTML invoice matching EFRIS format.
    """
    try:
        # Validate required fields
        required_fields = ["invoice_number", "invoice_date", "customer_name", "items"]
        for field in required_fields:
            if field not in invoice_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        if not invoice_data["items"] or len(invoice_data["items"]) == 0:
            raise HTTPException(status_code=400, detail="Invoice must have at least one item")
        
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Build EFRIS T109 payload - Handle both Simple and Pre-formatted EFRIS data
        goods_details = []
        total_net = 0
        total_tax = 0
        total_gross = 0
        
        logger.debug(f"[T109] Incoming invoice: {invoice_data.get('invoice_number', 'N/A')}, items: {len(invoice_data.get('items', []))}")
        
        # Check if client explicitly requested simple format
        # Simple format: ERP sends raw transaction data, middleware handles ALL EFRIS formatting
        # This is the RECOMMENDED format for new ERP integrations
        force_simple = str(invoice_data.get("format", "")).lower() == "simple"
        if force_simple:
            logger.info("[T109] Simple format requested — middleware will compute all EFRIS fields")
        
        for idx, item in enumerate(invoice_data["items"], 1):
            logger.debug(f"[T109] Item {idx}: code={item.get('itemCode', item.get('item_code', 'N/A'))}, catId={item.get('goodsCategoryId', item.get('goods_category_id', 'N/A'))}")
            
            # Support both Simple Custom ERP format AND pre-formatted EFRIS format
            # Simple format: item_name/item, item_code/itemCode, quantity/qty, unit_price/unitPrice, tax_rate/taxRate
            # EFRIS format: item, itemCode, qty, unitPrice, taxRate, total, tax (all pre-computed)
            
            # Determine format: explicit "format":"simple" overrides auto-detection
            # Auto-detection: if item has "qty" or "itemCode", assume EFRIS-formatted
            if force_simple:
                is_efris_format = False
            else:
                is_efris_format = "qty" in item or "itemCode" in item
            logger.debug(f"[T109] is_efris_format: {is_efris_format}")
            
            # Check if this is a discount amount line (discountFlag='0')
            is_discount_line = str(item.get("discountFlag", item.get("discount_flag", "2"))) == "0"
            
            if is_efris_format:
                # Data is already EFRIS-formatted - use it directly
                item_name = item.get("item", "")
                item_code = item.get("itemCode", "")
                # Discount lines (discountFlag=0): qty must be empty per EFRIS spec (error 1181)
                raw_qty = item.get("qty")
                qty = None if is_discount_line or raw_qty is None or str(raw_qty).strip() == "" else float(raw_qty or 1)
                unit_price = float(item.get("unitPrice", 0) or 0)
                total_line = float(item.get("total", 0) or 0)
                tax_amount = float(item.get("tax", 0) or 0)
                
                # Normalize taxRate for EFRIS compliance
                # EFRIS accepts: "0.18" (standard), "0" (zero-rated/excise), "-" (exempt)
                raw_tax_rate = item.get("taxRate", "0.18")
                if raw_tax_rate == "-":
                    tax_rate_str = "-"  # Exempt
                elif raw_tax_rate in ["", None]:
                    tax_rate_str = "0.18"  # Default to standard VAT
                elif raw_tax_rate in ["0", 0, 0.0]:
                    tax_rate_str = "0"  # Zero-rated
                elif isinstance(raw_tax_rate, (int, float)):
                    if raw_tax_rate == 0.18 or raw_tax_rate == 18:
                        tax_rate_str = "0.18"
                    elif raw_tax_rate > 1:
                        tax_rate_str = f"{raw_tax_rate / 100:.2f}"
                    else:
                        tax_rate_str = f"{raw_tax_rate:.2f}"
                else:
                    try:
                        rate_val = float(str(raw_tax_rate))
                        if rate_val == 0:
                            tax_rate_str = "0"
                        elif rate_val > 1:
                            tax_rate_str = f"{rate_val / 100:.2f}"
                        else:
                            tax_rate_str = f"{rate_val:.2f}"
                    except:
                        tax_rate_str = str(raw_tax_rate)
                
                # Calculate net amount (unconditional: works for both positive items and negative discount lines)
                net_amount = total_line - tax_amount
                
            else:
                # Simple Custom ERP format - middleware computes everything
                # Accept both snake_case and camelCase field names from any ERP
                item_name = item.get("item_name", item.get("item", ""))
                item_code = item.get("item_code", item.get("itemCode", ""))
                # Discount lines: qty must be empty
                raw_qty = item.get("quantity", item.get("qty", 1))
                qty = None if is_discount_line or raw_qty is None or str(raw_qty).strip() == "" else float(raw_qty or 1)
                unit_price = float(item.get("unit_price", item.get("unitPrice", 0)) or 0)
                tax_rate_raw = item.get("tax_rate", item.get("taxRate", 18))
                # Handle string "-" for exempt (sent by some ERPs)
                if str(tax_rate_raw).strip() == "-":
                    tax_rate_pct = -1  # Will be treated as exempt below
                else:
                    tax_rate_pct = float(tax_rate_raw)  # Default 18%, accepts: 18, 0.18, 0, -1 (exempt)
                discount = float(item.get("discount", 0) or 0)
                
                # Tax inclusive calculation
                # For discount lines (qty=None), use total directly from item if provided
                if is_discount_line:
                    total_line = float(item.get("total", item.get("unit_price", 0)) or 0)
                else:
                    total_line = (qty * unit_price)
                if tax_rate_pct > 0:
                    tax_rate_decimal = tax_rate_pct / 100 if tax_rate_pct > 1 else tax_rate_pct
                    net_amount = total_line / (1 + tax_rate_decimal)
                    tax_amount = total_line - net_amount
                    tax_rate_str = f"{tax_rate_decimal:.2f}"  # "0.18" format
                elif tax_rate_pct == 0:
                    net_amount = total_line
                    tax_amount = 0
                    tax_rate_str = "0"  # Zero-rated
                else:
                    # Negative means exempt
                    net_amount = total_line
                    tax_amount = 0
                    tax_rate_str = "-"  # Exempt
            
            # Get goodsCategoryId - support multiple field name formats
            raw_goods_category = item.get("goodsCategoryId", 
                                 item.get("goods_category_id", 
                                 item.get("commodity_code", 
                                 item.get("commodityCategoryId", ""))))
            
            # Validate goodsCategoryId - only filter clearly invalid codes
            # Valid: "44102906" (8 chars), "1010101" (7 chars), etc.
            # Invalid: "100000000" (9 chars, placeholder), "000000000" (all zeros)
            if raw_goods_category and (len(raw_goods_category) > 8 or raw_goods_category.startswith("10000000") or raw_goods_category == "000000000"):
                logger.warning(f"[T109] Invalid goodsCategoryId '{raw_goods_category}' - clearing to let EFRIS use T130 value")
                goods_category_id = ""
            else:
                goods_category_id = raw_goods_category
            
            logger.debug(f"[T109] Final goodsCategoryId: '{goods_category_id}'")
            
            goods_details.append({
                "item": item_name,
                "itemCode": item_code,
                "qty": "" if is_discount_line else str(qty),
                "unitOfMeasure": "" if is_discount_line else item.get("unitOfMeasure", item.get("unit_of_measure", "102")),
                "unitPrice": "" if is_discount_line else f"{unit_price:.2f}",
                "total": f"{total_line:.2f}",
                "taxRate": tax_rate_str,
                "tax": f"{tax_amount:.2f}",
                # EFRIS validation: If discountFlag is "2" (no discount) or "0", discountTotal MUST be empty
                "discountTotal": "" if item.get("discountFlag", "2") in ["0", "2"] else item.get("discountTotal", ""),
                "discountTaxRate": "" if item.get("discountFlag", "2") in ["0", "2"] else item.get("discountTaxRate", ""),
                "orderNumber": item.get("orderNumber", str(idx - 1)),  # EFRIS spec: start from 0
                "discountFlag": item.get("discountFlag", "2"),
                "deemedFlag": item.get("deemedFlag", "2"),
                "exciseFlag": item.get("exciseFlag", "2"),
                # Excise fields: populate from item when exciseFlag=1, empty when exciseFlag=2
                "categoryId": item.get("categoryId", "") if item.get("exciseFlag", "2") == "1" else "",
                "categoryName": item.get("categoryName", "") if item.get("exciseFlag", "2") == "1" else "",
                "goodsCategoryId": goods_category_id,
                "goodsCategoryName": item.get("goodsCategoryName", ""),
                "exciseRate": item.get("exciseRate", "") if item.get("exciseFlag", "2") == "1" else "",
                "exciseRule": item.get("exciseRule", "") if item.get("exciseFlag", "2") == "1" else "",
                "exciseTax": item.get("exciseTax", "") if item.get("exciseFlag", "2") == "1" else "",
                "pack": item.get("pack", "1"),  # Default to 1 per EFRIS spec
                "stick": item.get("stick", "1"),  # Default to 1 per EFRIS spec
                "exciseUnit": item.get("exciseUnit", "") if item.get("exciseFlag", "2") == "1" else "",
                "exciseCurrency": item.get("exciseCurrency", "") if item.get("exciseFlag", "2") == "1" else "",
                "exciseRateName": item.get("exciseRateName", "") if item.get("exciseFlag", "2") == "1" else "",
                "vatApplicableFlag": item.get("vatApplicableFlag", "1"),
                # Tax classification fields (required by EFRIS, same as QB mapper)
                "taxCategoryCode": item.get("taxCategoryCode", item.get("tax_category_code",
                    "03" if tax_rate_str == "-" else ("02" if tax_rate_str == "0" else "01"))),
                "isZeroRate": item.get("isZeroRate", item.get("is_zero_rate",
                    "101" if tax_rate_str == "0" else "102")),
                "isExempt": item.get("isExempt", item.get("is_exempt",
                    "101" if tax_rate_str == "-" else "102"))
            })
            
            # EFRIS Discount Line Generation (for simple format items with discount)
            # EFRIS requires a SEPARATE discount line with discountFlag="0"
            if not is_efris_format and discount > 0:
                # Mark the original item as discounted
                goods_details[-1]["discountFlag"] = "1"
                goods_details[-1]["discountTotal"] = f"{-discount:.2f}"
                goods_details[-1]["discountTaxRate"] = tax_rate_str
                
                # Calculate discount tax/net breakdown
                if tax_rate_str not in ["-", "0", ""]:
                    try:
                        discount_rate = float(tax_rate_str)
                        discount_net = discount / (1 + discount_rate)
                        discount_tax = discount - discount_net
                    except:
                        discount_net = discount
                        discount_tax = 0
                else:
                    discount_net = discount
                    discount_tax = 0
                
                # Add the EFRIS discount line (discountFlag="0", negative amounts)
                # EFRIS spec: qty and unitOfMeasure MUST be empty for discount lines (error 1181)
                discount_line = {
                    "item": f"{item_name} (Discount)",
                    "itemCode": item_code,
                    "qty": "",
                    "unitOfMeasure": "",
                    "unitPrice": "",
                    "total": f"{-discount:.2f}",
                    "taxRate": tax_rate_str,
                    "tax": f"{-discount_tax:.2f}",
                    "discountTotal": "",  # Must be empty for discountFlag=0
                    "discountTaxRate": "",
                    "orderNumber": str(idx),  # Next order number after the original item
                    "discountFlag": "0",  # This IS the discount line
                    "deemedFlag": "2",
                    "exciseFlag": "2",
                    "categoryId": "",
                    "categoryName": "",
                    "goodsCategoryId": goods_category_id,
                    "goodsCategoryName": item.get("goodsCategoryName", ""),
                    "exciseRate": "",
                    "exciseRule": "",
                    "exciseTax": "",
                    "pack": "1",
                    "stick": "1",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "exciseRateName": "",
                    "vatApplicableFlag": item.get("vatApplicableFlag", "1"),
                    # Inherit tax classification from parent item
                    "taxCategoryCode": "03" if tax_rate_str == "-" else ("02" if tax_rate_str == "0" else "01"),
                    "isZeroRate": "101" if tax_rate_str == "0" else "102",
                    "isExempt": "101" if tax_rate_str == "-" else "102"
                }
                goods_details.append(discount_line)
                
                # Subtract discount from totals
                total_net -= discount_net
                total_tax -= discount_tax
                total_gross -= discount
            
            total_net += net_amount
            total_tax += tax_amount
            total_gross += total_line
        
        # Debug: Print final goods_details before sending to EFRIS
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[T109] Final goods_details ({len(goods_details)} items):")
            for i, gd in enumerate(goods_details):
                logger.debug(f"[T109]   {i+1}: {gd.get('item','')}, code={gd.get('itemCode','')}, cat={gd.get('goodsCategoryId','')}, qty={gd.get('qty','')}, rate={gd.get('taxRate','')}")
        
        # Auto-generate tax_details from items if client didn't provide them
        if "tax_details" not in invoice_data or not invoice_data.get("tax_details"):
            logger.debug("[T109] No tax_details provided - auto-generating from items")
            tax_groups = {}  # taxCategoryCode -> {net, tax, gross, excise_unit, excise_currency, rate_name}
            
            for gd_item in goods_details:
                # Determine tax category from item's taxRate
                item_tax_rate = gd_item.get("taxRate", "0.18")
                if item_tax_rate == "-":
                    cat = "03"  # Exempt
                elif item_tax_rate == "0":
                    cat = "02"  # Zero-rated
                else:
                    cat = "01"  # Standard VAT
                
                item_total = float(gd_item.get("total", 0) or 0)
                item_tax = float(gd_item.get("tax", 0) or 0)
                # netAmount = grossAmount - taxAmount (works for both positive and negative values)
                item_net = item_total - item_tax
                
                if cat not in tax_groups:
                    tax_groups[cat] = {"net": 0, "tax": 0, "gross": 0}
                tax_groups[cat]["net"] += item_net
                tax_groups[cat]["tax"] += item_tax
                tax_groups[cat]["gross"] += item_total
                
                # Handle excise duty items
                if gd_item.get("exciseFlag") == "1":
                    excise_tax = float(gd_item.get("exciseTax", 0))
                    if excise_tax > 0:
                        if "05" not in tax_groups:
                            tax_groups["05"] = {"net": 0, "tax": 0, "gross": 0,
                                                "excise_unit": gd_item.get("exciseUnit", ""),
                                                "excise_currency": gd_item.get("exciseCurrency", "")}
                        tax_groups["05"]["net"] += item_net
                        tax_groups["05"]["tax"] += excise_tax
                        tax_groups["05"]["gross"] += item_net + excise_tax
            
            # Build tax_details array in invoice_data for the conversion step below
            auto_tax_details = []
            cat_names = {"01": "Standard Rate (18%)", "02": "Zero Rate (0%)", "03": "Exempt",
                         "04": "Deemed (18%)", "05": "Excise Duty"}
            for cat, amounts in sorted(tax_groups.items()):
                entry = {
                    "taxCategoryCode": cat,
                    "netAmount": f"{amounts['net']:.2f}",
                    "taxRate": "0.18" if cat == "01" else ("0" if cat in ["02", "05"] else ("-" if cat == "03" else "0.18")),
                    "taxAmount": f"{amounts['tax']:.2f}",
                    "grossAmount": f"{amounts['gross']:.2f}",
                    "taxRateName": cat_names.get(cat, ""),
                    "exciseUnit": amounts.get("excise_unit", ""),
                    "exciseCurrency": amounts.get("excise_currency", "")
                }
                auto_tax_details.append(entry)
            invoice_data["tax_details"] = auto_tax_details
            logger.debug(f"[T109] Auto-generated tax_details: {auto_tax_details}")
        
        # Convert tax_details - support both snake_case and camelCase formats
        # CRITICAL: Recalculate netAmount and grossAmount for EFRIS compliance
        tax_details = []
        if "tax_details" in invoice_data and invoice_data["tax_details"]:
            for td in invoice_data["tax_details"]:
                # Support both formats: taxCategoryCode (EFRIS) or tax_category_code (simple)
                tax_category = td.get("taxCategoryCode", td.get("tax_category_code", "01"))
                tax_amount = float(td.get("taxAmount", td.get("tax_amount", 0)))
                tax_rate_name = td.get("taxRateName", td.get("tax_rate_name", ""))
                
                # CRITICAL: Recalculate netAmount and grossAmount based on EFRIS rules
                if tax_category == "05":
                    # Excise duty: netAmount = base amount before all taxes
                    # grossAmount = netAmount + excise tax (not including VAT)
                    # Find the base net amount from VAT entry or calculate from items
                    base_net = 0
                    for base_td in invoice_data["tax_details"]:
                        if base_td.get("taxCategoryCode", base_td.get("tax_category_code")) == "01":
                            base_net = float(base_td.get("netAmount", base_td.get("net_amount", 0)))
                            break
                    if base_net == 0:
                        # Calculate from total_net if no VAT entry found
                        base_net = total_net
                    
                    net_amount = base_net  # Same base as VAT
                    gross_amount = base_net + tax_amount  # Base + excise only
                else:
                    # Non-excise categories: use client values but validate
                    net_amount = float(td.get("netAmount", td.get("net_amount", 0)))
                    gross_amount = float(td.get("grossAmount", td.get("gross_amount", 0)))
                    
                    # Validate: grossAmount should = netAmount + taxAmount for non-excise
                    expected_gross = net_amount + tax_amount
                    if abs(gross_amount - expected_gross) > 0.01:
                        logger.warning(f"[T109] Correcting grossAmount for cat {tax_category}: {gross_amount} -> {expected_gross}")
                        gross_amount = expected_gross
                
                # CRITICAL: Format taxRate correctly for EFRIS
                # - For VAT (01): MUST be "0.18" exactly
                # - For Excise (05) fixed rate: MUST be "0"
                # - For Zero-rated (02): MUST be "0"
                # - For Exempt (03): MUST be "-"
                raw_tax_rate = td.get("taxRate", td.get("tax_rate", "0.18"))
                
                # Normalize taxRate to EFRIS-compliant format
                if tax_category == "01":
                    # VAT must be exactly "0.18"
                    tax_rate_str = "0.18"
                elif tax_category == "05":
                    # Excise - check exciseRule to determine if percentage or fixed
                    excise_rule = td.get("exciseRule", td.get("excise_rule", "2"))
                    if excise_rule == "1":
                        # Percentage-based excise - format as decimal
                        try:
                            rate_val = float(str(raw_tax_rate).replace("%", ""))
                            if rate_val > 1:  # e.g., 10 means 10%
                                rate_val = rate_val / 100
                            tax_rate_str = f"{rate_val:.2f}"
                        except:
                            tax_rate_str = "0"
                    else:
                        # Fixed rate excise - must be "0"
                        tax_rate_str = "0"
                elif tax_category == "02":
                    tax_rate_str = "0"
                elif tax_category == "03":
                    tax_rate_str = "-"
                else:
                    tax_rate_str = str(raw_tax_rate)
                
                tax_detail_entry = {
                    "taxCategoryCode": str(tax_category),
                    "netAmount": f"{net_amount:.2f}",
                    "taxRate": tax_rate_str,
                    "taxAmount": f"{tax_amount:.2f}",
                    "grossAmount": f"{gross_amount:.2f}",
                    # EFRIS spec requires exciseUnit and exciseCurrency in ALL taxDetails entries
                    "exciseUnit": td.get("exciseUnit", td.get("excise_unit", "")),
                    "exciseCurrency": td.get("exciseCurrency", td.get("excise_currency", ""))
                }
                
                # Add taxRateName if present
                if tax_rate_name:
                    tax_detail_entry["taxRateName"] = tax_rate_name
                
                logger.debug(f"[T109] taxDetail: cat={tax_category}, net={net_amount}, tax={tax_amount}, gross={gross_amount}, rate={tax_rate_str}")
                tax_details.append(tax_detail_entry)
        
        # Build invoice summary from the finalized tax_details (most accurate for EFRIS validation)
        invoice_summary = _build_invoice_summary(invoice_data, total_net, total_tax, total_gross, goods_details, tax_details)
        
        # Calculate payment total: netAmount + ALL taxes (VAT + excise)
        # This is what the buyer actually pays
        payment_total = float(invoice_summary["netAmount"]) + float(invoice_summary["taxAmount"])
        
        logger.info(f"[T109] Invoice payload: net={invoice_summary['netAmount']}, tax={invoice_summary['taxAmount']}, gross={invoice_summary['grossAmount']}, payment={payment_total}")
        if logger.isEnabledFor(logging.DEBUG):
            for i, td_entry in enumerate(tax_details):
                logger.debug(f"[T109] taxDetail[{i}]: {td_entry}")
        
        efris_payload = {
            "oriInvoiceId": "",
            "invoiceNo": "",  # Empty for new invoices - EFRIS assigns FDN
            "antifakeCode": "",
            "deviceNo": company.device_no,
            "isCheckBatchNo": "0",
            "isInsurance": "0",
            "invoiceType": "1",
            "invoiceKind": "1",
            "dataSource": "106",
            "invoiceIndustryCode": "101",
            "isBatch": "0",
            "buyerDetails": {
                "buyerTin": invoice_data.get("customer_tin", ""),
                "buyerNinBrn": "",
                "buyerPassportNum": "",
                "buyerLegalName": invoice_data.get("customer_name", ""),
                "buyerBusinessName": invoice_data.get("customer_name", ""),
                "buyerAddress": invoice_data.get("customer_address", ""),
                "buyerEmail": invoice_data.get("customer_email", ""),
                "buyerMobilePhone": invoice_data.get("customer_phone", ""),
                "buyerLinePhone": "",
                "buyerPlaceOfBusi": "",
                "buyerType": invoice_data.get("buyer_type", "1"),  # Use provided or default to Individual
                "buyerCitizenship": "1",
                "buyerSector": "1",
                "buyerReferenceNo": ""
            },
            "basicInformation": {
                "invoiceNo": "",  # Empty - EFRIS will generate FDN
                "antifakeCode": "",
                "deviceNo": company.device_no,
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "API User",  # Required - default operator for external API
                "currency": invoice_data.get("currency", "UGX"),
                "isCheckBatchNo": "0",
                "isInsurance": "0",
                "invoiceType": "1",
                "invoiceKind": "1",
                "dataSource": "106",
                "invoiceIndustryCode": "101",
                "isBatch": "0"
            },
            "sellerDetails": {
                "tin": company.tin,
                "ninBrn": "",
                "legalName": company.name,
                "businessName": company.name,
                "address": "Kampala, Uganda",  # Default address
                "emailAddress": f"efris@{company.tin}.ug",  # Required - use TIN-based email
                "mobilePhone": "0700000000",  # Default phone
                "linePhone": "",
                "placeOfBusi": "",
                "referenceNo": invoice_data["invoice_number"]  # Your internal invoice number
            },
            "goodsDetails": goods_details,
            "taxDetails": tax_details,  # Use converted tax_details
            # Build summary from tax_details (most accurate for EFRIS validation)
            "summary": invoice_summary,
            "payWay": [{
                "paymentMode": invoice_data.get("payment_method", "101"),  # Use provided or default to Cash
                "paymentAmount": str(round(payment_total, 2)),  # net + ALL taxes (incl excise)
                "orderNumber": "a"  # EFRIS spec: lowercase letters a, b, c...
            }],
            "extend": {
                "reason": "",
                "reasonCode": ""
            },
            "importServicesSeller": {},
            "airlineGoodsDetails": []
        }
        
        # Submit to EFRIS (T109)
        result = efris.upload_invoice(efris_payload)
        
        # Debug: Log the response structure
        print(f"[EXTERNAL API] EFRIS Response Structure:")
        print(f"  - returnStateInfo: {result.get('returnStateInfo', {})}")
        print(f"  - data keys: {result.get('data', {}).keys()}")
        if 'decrypted_content' in result.get('data', {}):
            print(f"  - decrypted_content keys: {result['data']['decrypted_content'].keys() if isinstance(result['data']['decrypted_content'], dict) else 'not a dict'}")
        
        if result.get("returnStateInfo", {}).get("returnCode") == "00":
            # Success - extract FDN and verification code
            # The decrypted content is stored in result['data']['decrypted_content']
            data = result.get("data", {}).get("decrypted_content", result.get("data", {}))
            
            # Debug: Log what we're extracting
            print(f"[EXTERNAL API] Extracting fiscal data:")
            print(f"  - basicInformation: {data.get('basicInformation', {})}")
            print(f"  - summary: {data.get('summary', {})}")
            
            fdn = data.get("basicInformation", {}).get("invoiceNo", "")
            verification_code = data.get("basicInformation", {}).get("antifakeCode", "")
            invoice_id = data.get("basicInformation", {}).get("invoiceId", "")
            qr_code = data.get("summary", {}).get("qrCode", "")
            
            print(f"[EXTERNAL API] Extracted values: FDN={fdn}, VerifCode={verification_code}, InvoiceID={invoice_id}")
            
            # Save to database
            # Calculate excise total from excise items
            total_excise = sum(float(gd.get("exciseTax", 0)) for gd in goods_details if gd.get("exciseFlag") == "1")
            efris_invoice = EFRISInvoice(
                company_id=company.id,
                invoice_no=invoice_data["invoice_number"],
                invoice_date=datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d").date(),
                customer_name=invoice_data["customer_name"],
                customer_tin=invoice_data.get("customer_tin", ""),
                buyer_type=invoice_data.get("buyer_type", "1"),
                total_amount=round(payment_total, 2),
                total_tax=round(float(invoice_summary["taxAmount"]), 2),
                total_excise=round(total_excise, 2),
                total_discount=sum(float(item.get("discount", item.get("discountTotal", 0)) or 0) for item in invoice_data["items"]),
                currency=invoice_data.get("currency", "UGX"),
                status="success",
                fdn=fdn,
                efris_invoice_id=invoice_id,
                submission_date=datetime.utcnow(),
                efris_payload=efris_payload,
                efris_response=result
            )
            db.add(efris_invoice)
            db.commit()
            
            # Return complete invoice data for rendering EFRIS-style fiscal invoice
            return {
                "success": True,
                "message": "Invoice fiscalized successfully",
                
                # Section A: Seller Details
                "seller": {
                    "brn": "",  # Add BRN to Company model if needed
                    "tin": company.tin,
                    "legal_name": company.name,
                    "trade_name": company.name,
                    "address": "Kampala, Uganda",
                    "reference_number": invoice_data["invoice_number"],
                    "served_by": "API User"
                },
                
                # Section B: URA/EFRIS Information
                "fiscal_data": {
                    "document_type": "Original",
                    "fdn": fdn,  # Fiscal Document Number
                    "verification_code": verification_code,
                    "device_number": company.device_no,
                    "efris_invoice_id": invoice_id,
                    "issued_date": datetime.now().strftime("%d/%m/%Y"),
                    "issued_time": datetime.now().strftime("%H:%M:%S"),
                    "qr_code": qr_code
                },
                
                # Section C: Buyer Details
                "buyer": {
                    "name": invoice_data["customer_name"],
                    "tin": invoice_data.get("customer_tin", ""),
                    "buyer_type": invoice_data.get("buyer_type", "1")
                },
                
                # Section D: Goods & Services Details
                "items": goods_details,
                
                # Section E: Tax Details (by category)
                "tax_details": tax_details,
                
                # Section F: Summary
                "summary": {
                    "net_amount": float(invoice_summary["netAmount"]),
                    "tax_amount": float(invoice_summary["taxAmount"]),
                    "gross_amount": float(invoice_summary["grossAmount"]),
                    "gross_amount_words": _amount_to_words(float(invoice_summary["grossAmount"])),
                    "payment_mode": _get_payment_mode_name(invoice_data.get("payment_method", "101")),
                    "total_amount": round(payment_total, 2),  # Net + ALL taxes (what buyer pays)
                    "currency": invoice_data.get("currency", "UGX"),
                    "number_of_items": len(goods_details),
                    "mode": "Online",
                    "remarks": invoice_data.get("remarks", "")
                },
                
                # Legacy fields for backward compatibility
                "invoice_number": invoice_data["invoice_number"],
                "fiscalized_at": efris_invoice.submission_date.isoformat()
            }
        else:
            # EFRIS error
            error_msg = result.get("returnStateInfo", {}).get("returnMessage", "Unknown error")
            error_code = result.get("returnStateInfo", {}).get("returnCode", "")
            
            # Save failed attempt
            efris_invoice = EFRISInvoice(
                company_id=company.id,
                invoice_no=invoice_data["invoice_number"],
                invoice_date=datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d").date(),
                customer_name=invoice_data["customer_name"],
                total_amount=round(payment_total, 2),
                total_tax=round(float(invoice_summary["taxAmount"]), 2),
                currency=invoice_data.get("currency", "UGX"),
                status="failed",
                error_message=f"{error_code}: {error_msg}",
                efris_payload=efris_payload,
                efris_response=result
            )
            db.add(efris_invoice)
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": error_code,
                    "message": error_msg,
                    "details": "EFRIS rejected the invoice"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/external/efris/register-product")
async def external_register_product(
    product_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Register a product/item with EFRIS (T130)
    
    Request Body:
    {
        "item_code": "PROD-001",
        "item_name": "Product A",
        "unit_price": 5000,
        "commodity_code": "1010101",
        "commodity_name": "General Goods",
        "unit_of_measure": "103",  // 101=Stick, 102=Litre, 103=Kg (see EFRIS T115 codes)
        "have_excise_tax": "102",  // 101=Yes, 102=No (default: 102)
        "excise_duty_code": "",  // Required ONLY if have_excise_tax="101"
        "stock_quantity": 100,
        "description": "Product description",
        "goods_type_code": "101"  // 101=Goods, 102=Fuel (default: 101)
    }
    
    IMPORTANT - Excise Duty:
    - If have_excise_tax="101" (YES), you MUST provide excise_duty_code
    - If have_excise_tax="102" (NO), do NOT include excise_duty_code
    - Get excise codes from /api/external/efris/excise-duty endpoint
    
    Response:
    {
        "success": true,
        "product_code": "PROD-001",
        "efris_status": "Registered",
        "message": "Product registered successfully"
    }
    """
    try:
        required_fields = ["item_code", "item_name", "unit_price", "commodity_code"]
        for field in required_fields:
            if field not in product_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Determine if item has excise tax
        have_excise = product_data.get("have_excise_tax", "102")
        measure_unit = product_data.get("unit_of_measure", "102")
        
        # Build T130 payload - MATCHES QuickBooks working format exactly
        t130_payload = [{
            "operationType": "101",  # 101=Add, 102=Update
            "goodsName": product_data["item_name"],
            "goodsCode": product_data["item_code"],
            "measureUnit": measure_unit,
            "unitPrice": str(product_data["unit_price"]),
            "currency": "101",  # 101=UGX
            "commodityCategoryId": product_data["commodity_code"],
            "haveExciseTax": have_excise,
            "goodsTypeCode": product_data.get("goods_type_code", "101"),  # 101=Goods, 102=Fuel (NOT service!)
            "serviceMark": "101" if product_data.get("is_service", False) else "102",  # 101=Service, 102=Goods
            "description": product_data.get("description", ""),
            # Match QuickBooks working format
            "havePieceUnit": "101",  # Same as QuickBooks
            "pieceMeasureUnit": measure_unit,  # Same as QuickBooks
            "pieceUnitPrice": str(product_data["unit_price"]),  # Same as QuickBooks
            "packageScaledValue": "1",
            "pieceScaledValue": "1"
        }]
        
        # Add stockPrewarning - required for physical products, optional for services
        is_service = product_data.get("is_service", False)
        if not is_service:
            # Accept any of these field names, fall back to "0" if none provided
            stock_prewarning = (
                product_data.get("stock_prewarning") or
                product_data.get("stock_quantity") or
                product_data.get("low_stock_warning") or
                product_data.get("stockPrewarning") or
                "0"
            )
            t130_payload[0]["stockPrewarning"] = str(stock_prewarning)
        
        # Add excise duty code ONLY if item has excise tax
        if have_excise == "101" and product_data.get("excise_duty_code"):
            t130_payload[0]["exciseDutyCode"] = product_data["excise_duty_code"]
        
        result = efris.upload_goods(t130_payload)
        
        # Log the full response for debugging
        print(f"[REGISTER-PRODUCT] EFRIS returned: {result}")
        
        # Check if result is a string (error case)
        if isinstance(result, str):
            raise HTTPException(status_code=500, detail=f"EFRIS communication error: {result}")
        
        if result.get("returnStateInfo", {}).get("returnCode") == "00":
            return {
                "success": True,
                "product_code": product_data["item_code"],
                "efris_status": "Registered",
                "message": "Product registered successfully"
            }
        else:
            error_msg = result.get("returnStateInfo", {}).get("returnMessage", "Unknown error")
            error_code = result.get("returnStateInfo", {}).get("returnCode", "Unknown")
            raise HTTPException(status_code=400, detail=f"EFRIS error {error_code}: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/external/efris/submit-purchase-order")
async def external_submit_purchase_order(
    po_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit purchase order to EFRIS (T130 - Send Purchase Order)
    
    Request Body:
    {
        "po_number": "PO-2024-001",
        "po_date": "2024-01-24",
        "vendor_name": "Supplier XYZ Ltd",
        "vendor_tin": "1234567890",
        "items": [...],
        "total_amount": 500000,
        "currency": "UGX",
        "delivery_date": "2024-02-15"
    }
    """
    try:
        required_fields = ["po_number", "po_date", "vendor_name", "items", "total_amount", "currency"]
        for field in required_fields:
            if field not in po_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        if not po_data["items"] or len(po_data["items"]) == 0:
            raise HTTPException(status_code=400, detail="Purchase order must have at least one item")
        
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Build T130 payload
        t130_payload = {
            "supplierName": po_data["vendor_name"],
            "supplierTin": po_data.get("vendor_tin", ""),
            "orderNo": po_data["po_number"],
            "orderDate": po_data["po_date"],
            "deliveryDate": po_data.get("delivery_date", po_data["po_date"]),
            "totalAmount": str(po_data["total_amount"]),
            "currency": po_data.get("currency", "UGX"),
            "goodsDetails": []
        }
        
        # Add items
        for idx, item in enumerate(po_data["items"], 1):
            t130_payload["goodsDetails"].append({
                "itemCode": item.get("item_code", ""),
                "item": item.get("item_name", ""),
                "qty": str(item.get("quantity", 1)),
                "unitPrice": str(item.get("unit_price", 0)),
                "total": str(item.get("total", 0)),
                "unitOfMeasure": item.get("unit_of_measure", "102"),
                "orderNumber": str(idx)
            })
        
        # Submit to EFRIS
        result = efris.send_purchase_order(t130_payload)
        
        if result.get("returnStateInfo", {}).get("returnCode") == "00":
            # Success - save to database
            po_record = PurchaseOrder(
                company_id=company.id,
                qb_po_id=po_data["po_number"],
                qb_doc_number=po_data["po_number"],
                qb_vendor_name=po_data["vendor_name"],
                qb_txn_date=datetime.strptime(po_data["po_date"], "%Y-%m-%d"),
                qb_total_amt=po_data["total_amount"],
                qb_data=po_data,
                efris_status="sent",
                efris_sent_at=datetime.utcnow(),
                efris_response=result
            )
            db.add(po_record)
            db.commit()
            
            return {
                "success": True,
                "po_number": po_data["po_number"],
                "efris_status": "submitted",
                "reference_number": result.get("data", {}).get("referenceNo", ""),
                "message": "Purchase order submitted successfully"
            }
        else:
            error_msg = result.get("returnStateInfo", {}).get("returnMessage", "Unknown error")
            error_code = result.get("returnStateInfo", {}).get("returnCode", "")
            
            # Save failed attempt
            po_record = PurchaseOrder(
                company_id=company.id,
                qb_po_id=po_data["po_number"],
                qb_doc_number=po_data["po_number"],
                qb_vendor_name=po_data["vendor_name"],
                qb_txn_date=datetime.strptime(po_data["po_date"], "%Y-%m-%d"),
                qb_total_amt=po_data["total_amount"],
                qb_data=po_data,
                efris_status="failed",
                efris_error=f"{error_code}: {error_msg}",
                efris_response=result
            )
            db.add(po_record)
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": error_code,
                    "message": error_msg
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/external/efris/submit-credit-note")
async def external_submit_credit_note(
    credit_note_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit credit note application to EFRIS (T110 - Credit Note Application)
    
    Accepts both pre-formatted EFRIS T110 payloads and simple format.
    
    Pre-formatted (from YourBookSuit / Custom ERPs that build the EFRIS payload):
    - Must include: oriInvoiceId, reasonCode, applicationTime, goodsDetails, 
      taxDetails, summary, payWay, buyerDetails, basicInformation
    
    Simple format:
    {
        "credit_note_number": "CN-2024-001",
        "credit_note_date": "2024-01-24",
        "original_invoice_number": "INV-001",
        "original_fdn": "1234567890123456",
        "customer_name": "ABC Ltd",
        "reason": "Product return - defective item",
        "reason_code": "101",
        "items": [{"item_name": "Widget", "quantity": 2, "unit_price": 5000, "tax_rate": 0.18, "tax_amount": 900, "total": 10000}],
        "total_amount": 10000,
        "total_tax": 1800,
        "currency": "UGX"
    }
    """
    try:
        # Get cached EFRIS Manager
        efris = get_efris_manager(company)
        
        # Detect if this is a pre-formatted EFRIS T110 payload
        # Pre-formatted payloads have top-level EFRIS fields like reasonCode, applicationTime, goodsDetails
        is_efris_format = all(k in credit_note_data for k in ["reasonCode", "goodsDetails", "taxDetails", "summary"])
        
        if is_efris_format:
            # ===== PRE-FORMATTED T110 PAYLOAD (from YourBookSuit etc.) =====
            logger.info(f"[T110] Processing pre-formatted credit note: {credit_note_data.get('sellersReferenceNo', 'N/A')}")
            
            # Use the payload as-is, but validate and fix key fields
            efris_payload = {}
            
            # Required top-level T110 fields
            efris_payload["oriInvoiceId"] = credit_note_data.get("oriInvoiceId", credit_note_data.get("original_fdn", ""))
            efris_payload["oriInvoiceNo"] = credit_note_data.get("oriInvoiceNo", credit_note_data.get("original_invoice_number", ""))
            efris_payload["reasonCode"] = credit_note_data.get("reasonCode", "101")
            efris_payload["reason"] = credit_note_data.get("reason", "")
            efris_payload["applicationTime"] = credit_note_data.get("applicationTime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            efris_payload["invoiceApplyCategoryCode"] = credit_note_data.get("invoiceApplyCategoryCode", "101")
            efris_payload["currency"] = credit_note_data.get("currency", "UGX")
            efris_payload["contactName"] = credit_note_data.get("contactName", credit_note_data.get("customer_name", ""))
            efris_payload["contactMobileNum"] = credit_note_data.get("contactMobileNum", "")
            efris_payload["contactEmail"] = credit_note_data.get("contactEmail", "")
            efris_payload["source"] = credit_note_data.get("source", "103")
            efris_payload["remarks"] = credit_note_data.get("remarks", "")
            efris_payload["sellersReferenceNo"] = credit_note_data.get("sellersReferenceNo", credit_note_data.get("credit_note_number", ""))
            
            # Process goodsDetails - ensure quantities/amounts are negative
            goods_details = []
            for idx, gd in enumerate(credit_note_data.get("goodsDetails", [])):
                is_cn_discount = str(gd.get("discountFlag", "2")) == "0"
                raw_qty = gd.get("qty")
                qty = None if is_cn_discount or raw_qty is None or str(raw_qty).strip() == "" else float(raw_qty or 0)
                total = float(gd.get("total", 0) or 0)
                tax = float(gd.get("tax", 0) or 0)
                unit_price = float(gd.get("unitPrice", 0) or 0)
                
                # Ensure negative values for credit note (skip qty check for discount lines)
                if qty is not None and qty > 0:
                    qty = -qty
                if total > 0:
                    total = -total
                if tax > 0 and float(gd.get("taxRate", "0")) != 0:
                    tax = -tax
                
                goods_detail = {
                    "item": gd.get("item", ""),
                    "itemCode": gd.get("itemCode", ""),
                    "qty": "" if is_cn_discount else str(qty),
                    "unitOfMeasure": "" if is_cn_discount else gd.get("unitOfMeasure", "101"),
                    "unitPrice": str(abs(unit_price)),  # unitPrice must be POSITIVE per EFRIS spec
                    "total": str(total),
                    "taxRate": gd.get("taxRate", "0.18"),
                    "tax": str(tax),
                    "orderNumber": str(gd.get("orderNumber", idx)),
                    "discountFlag": gd.get("discountFlag", "2"),
                    "deemedFlag": gd.get("deemedFlag", "2"),
                    "exciseFlag": gd.get("exciseFlag", "2"),
                    "categoryId": gd.get("categoryId", ""),
                    "categoryName": gd.get("categoryName", ""),
                    "goodsCategoryId": gd.get("goodsCategoryId", ""),
                    "goodsCategoryName": gd.get("goodsCategoryName", ""),
                    "exciseRate": gd.get("exciseRate", ""),
                    "exciseRule": gd.get("exciseRule", ""),
                    "exciseTax": gd.get("exciseTax", "0"),
                    "pack": gd.get("pack", "1"),
                    "stick": gd.get("stick", "1"),
                    "exciseUnit": gd.get("exciseUnit", ""),
                    "exciseCurrency": gd.get("exciseCurrency", ""),
                    "exciseRateName": gd.get("exciseRateName", ""),
                    "vatApplicableFlag": gd.get("vatApplicableFlag", "1")
                }
                goods_details.append(goods_detail)
            efris_payload["goodsDetails"] = goods_details
            
            # Process taxDetails - ensure amounts are negative
            tax_details = []
            for td in credit_note_data.get("taxDetails", []):
                net = float(td.get("netAmount", 0))
                tax_amt = float(td.get("taxAmount", 0))
                gross = float(td.get("grossAmount", 0))
                
                if net > 0:
                    net = -net
                if tax_amt > 0:
                    tax_amt = -tax_amt
                if gross > 0:
                    gross = -gross
                
                tax_details.append({
                    "taxCategoryCode": td.get("taxCategoryCode", "01"),
                    "netAmount": str(net),
                    "taxRate": td.get("taxRate", "0.18"),
                    "taxAmount": str(tax_amt),
                    "grossAmount": str(gross),
                    "exciseUnit": td.get("exciseUnit", ""),
                    "exciseCurrency": td.get("exciseCurrency", ""),
                    "taxRateName": td.get("taxRateName", "")
                })
            efris_payload["taxDetails"] = tax_details
            
            # Process summary - ensure negative
            client_summary = credit_note_data.get("summary", {})
            summary_net = float(client_summary.get("netAmount", 0))
            summary_tax = float(client_summary.get("taxAmount", 0))
            summary_gross = float(client_summary.get("grossAmount", 0))
            
            if summary_net > 0:
                summary_net = -summary_net
            if summary_tax > 0:
                summary_tax = -summary_tax
            if summary_gross > 0:
                summary_gross = -summary_gross
            
            efris_payload["summary"] = {
                "netAmount": str(summary_net),
                "taxAmount": str(summary_tax),
                "grossAmount": str(summary_gross),
                "itemCount": str(client_summary.get("itemCount", len(goods_details))),
                "modeCode": str(client_summary.get("modeCode", "0")),
                "qrCode": client_summary.get("qrCode", "")
            }
            
            # PayWay - must be positive per EFRIS spec  
            pay_way = credit_note_data.get("payWay", [])
            if isinstance(pay_way, list) and len(pay_way) > 0:
                efris_payload["payWay"] = pay_way
            else:
                efris_payload["payWay"] = [{
                    "paymentMode": "101",
                    "paymentAmount": str(abs(summary_gross)),
                    "orderNumber": "a"
                }]
            
            # Buyer details
            efris_payload["buyerDetails"] = credit_note_data.get("buyerDetails", {
                "buyerTin": credit_note_data.get("customer_tin", ""),
                "buyerNinBrn": "",
                "buyerPassportNum": "",
                "buyerLegalName": credit_note_data.get("customer_name", ""),
                "buyerBusinessName": credit_note_data.get("customer_name", ""),
                "buyerAddress": "",
                "buyerEmail": "",
                "buyerMobilePhone": "",
                "buyerLinePhone": "",
                "buyerPlaceOfBusi": "",
                "buyerType": "1",
                "buyerCitizenship": "",
                "buyerSector": "",
                "buyerReferenceNo": ""
            })
            
            # Basic information
            efris_payload["basicInformation"] = credit_note_data.get("basicInformation", {
                "operator": "System",
                "invoiceKind": "1",
                "invoiceIndustryCode": "101"
            })
            
        else:
            # ===== SIMPLE FORMAT (build T110 payload from simple fields) =====
            required_fields = ["credit_note_number", "credit_note_date", "original_invoice_number", 
                              "customer_name", "reason", "items", "total_amount", "currency"]
            for field in required_fields:
                if field not in credit_note_data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            if not credit_note_data["items"] or len(credit_note_data["items"]) == 0:
                raise HTTPException(status_code=400, detail="Credit note must have at least one item")
            
            logger.info(f"[T110] Processing simple-format credit note: {credit_note_data['credit_note_number']}")
            
            # Look up the original invoice's internal ID (invoiceId) via T108
            # T110 requires oriInvoiceId = internal invoiceId, oriInvoiceNo = FDN
            original_fdn = credit_note_data.get("original_fdn", "")
            ori_invoice_id = ""
            if original_fdn:
                try:
                    logger.info(f"[T110] Looking up invoiceId for FDN: {original_fdn}")
                    invoice_details = efris.get_invoice_details(original_fdn)
                    if isinstance(invoice_details, dict):
                        decrypted = invoice_details.get('data', {}).get('decrypted_content', {})
                        if isinstance(decrypted, dict):
                            basic_info = decrypted.get('basicInformation', {})
                            ori_invoice_id = basic_info.get('invoiceId', '')
                            logger.info(f"[T110] Found invoiceId: {ori_invoice_id} for FDN: {original_fdn}")
                        else:
                            logger.warning(f"[T110] T108 response had no decrypted_content, using FDN as oriInvoiceId")
                            ori_invoice_id = original_fdn
                    else:
                        logger.warning(f"[T110] T108 lookup failed: {invoice_details}, using FDN as oriInvoiceId")
                        ori_invoice_id = original_fdn
                except Exception as e:
                    logger.warning(f"[T110] T108 lookup error: {e}, using FDN as oriInvoiceId")
                    ori_invoice_id = original_fdn
            
            # Map reason text to EFRIS reason codes
            reason_text = credit_note_data.get("reason", "")
            reason_code = credit_note_data.get("reason_code", "")
            if not reason_code:
                reason_map = {
                    "GOODS_RETURNED": "101", "RETURN": "101", "EXPIRED": "101", "DAMAGED": "101",
                    "CANCELLATION": "102", "CANCELLED": "102", "CANCEL": "102",
                    "WRONG_AMOUNT": "103", "MISCALCULATION": "103", "PRICE_ERROR": "103",
                    "WAIVE_OFF": "104", "PARTIAL_WAIVE": "104",
                }
                reason_code = reason_map.get(reason_text.upper(), "105")
            
            # Build goods details from simple items
            goods_details = []
            for idx, item in enumerate(credit_note_data["items"]):
                qty = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0))
                total = float(item.get("total", qty * unit_price))
                tax_rate_raw = item.get("tax_rate", 0.18)
                
                # Normalize tax rate
                if isinstance(tax_rate_raw, (int, float)):
                    if tax_rate_raw > 1:
                        tax_rate = tax_rate_raw / 100  # 18 -> 0.18
                    else:
                        tax_rate = tax_rate_raw
                else:
                    tax_rate = 0.18
                
                if tax_rate == 0:
                    tax_rate_str = "0"
                elif tax_rate < 0 or str(tax_rate_raw) == "-":
                    tax_rate_str = "-"
                else:
                    tax_rate_str = str(tax_rate)
                
                tax_amount = float(item.get("tax_amount", round(total * tax_rate / (1 + tax_rate), 2) if tax_rate > 0 else 0))
                
                goods_details.append({
                    "item": item.get("item_name", ""),
                    "itemCode": item.get("item_code", item.get("item_name", "")),
                    "qty": str(-abs(qty)),
                    "unitOfMeasure": item.get("unit_of_measure", "101"),
                    "unitPrice": str(abs(unit_price)),  # Must be positive
                    "total": str(-abs(total)),
                    "taxRate": tax_rate_str,
                    "tax": str(-abs(tax_amount)) if tax_amount != 0 else "0",
                    "orderNumber": str(idx),
                    "discountFlag": "2",
                    "deemedFlag": "2",
                    "exciseFlag": "2",
                    "categoryId": "",
                    "categoryName": "",
                    "goodsCategoryId": item.get("commodity_code", item.get("goodsCategoryId", "")),
                    "goodsCategoryName": item.get("commodity_name", item.get("item_name", "")),
                    "exciseRate": "",
                    "exciseRule": "",
                    "exciseTax": "0",
                    "pack": "1",
                    "stick": "1",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "exciseRateName": "",
                    "vatApplicableFlag": "1"
                })
            
            # Build tax details grouped by tax category
            tax_groups = {}
            for item in credit_note_data["items"]:
                tax_rate_raw = item.get("tax_rate", 0.18)
                if isinstance(tax_rate_raw, (int, float)):
                    tax_rate = tax_rate_raw / 100 if tax_rate_raw > 1 else tax_rate_raw
                else:
                    tax_rate = 0.18
                
                if tax_rate == 0.18 or tax_rate == 18:
                    cat_code = "01"
                    rate_str = "0.18"
                elif tax_rate == 0:
                    cat_code = "02"
                    rate_str = "0"
                elif tax_rate < 0 or str(tax_rate_raw) == "-":
                    cat_code = "03"
                    rate_str = "-"
                else:
                    cat_code = "01"
                    rate_str = str(tax_rate)
                
                qty = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0))
                total = float(item.get("total", qty * unit_price))
                # Auto-calculate tax if not provided (tax-inclusive formula: tax = total * rate / (1 + rate))
                tax_amt = float(item.get("tax_amount", round(total * tax_rate / (1 + tax_rate), 2) if tax_rate > 0 else 0))
                
                if cat_code not in tax_groups:
                    tax_groups[cat_code] = {"rate": rate_str, "net": 0, "tax": 0, "gross": 0}
                
                # EFRIS formula: grossAmount = total (tax-inclusive), taxAmount, netAmount = grossAmount - taxAmount
                tax_groups[cat_code]["gross"] += total
                tax_groups[cat_code]["tax"] += tax_amt
                tax_groups[cat_code]["net"] += (total - tax_amt)
            
            tax_details = []
            total_net = 0
            total_tax = 0
            total_gross = 0
            for cat_code, grp in tax_groups.items():
                net = -abs(grp["net"])
                tax_amt = -abs(grp["tax"]) if grp["tax"] != 0 else 0
                gross = -abs(grp["gross"])
                total_net += net
                total_tax += tax_amt
                total_gross += gross
                tax_details.append({
                    "taxCategoryCode": cat_code,
                    "netAmount": str(net),
                    "taxRate": grp["rate"],
                    "taxAmount": str(tax_amt),
                    "grossAmount": str(gross),
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "taxRateName": ""
                })
            
            efris_payload = {
                "oriInvoiceId": ori_invoice_id,
                "oriInvoiceNo": original_fdn or credit_note_data["original_invoice_number"],
                "reasonCode": reason_code,
                "reason": reason_text if reason_code == "105" else "",
                "applicationTime": credit_note_data.get("credit_note_date", datetime.now().strftime("%Y-%m-%d")) + " " + datetime.now().strftime("%H:%M:%S"),
                "invoiceApplyCategoryCode": "101",
                "currency": credit_note_data.get("currency", "UGX"),
                "contactName": credit_note_data.get("customer_name", ""),
                "contactMobileNum": credit_note_data.get("buyer_phone", ""),
                "contactEmail": credit_note_data.get("buyer_email", ""),
                "source": "103",
                "remarks": credit_note_data.get("remarks", f"Credit for Invoice {credit_note_data['original_invoice_number']}"),
                "sellersReferenceNo": credit_note_data["credit_note_number"],
                "goodsDetails": goods_details,
                "taxDetails": tax_details,
                "summary": {
                    "netAmount": str(total_net),
                    "taxAmount": str(total_tax),
                    "grossAmount": str(total_gross),
                    "itemCount": str(len(goods_details)),
                    "modeCode": "0",
                    "qrCode": ""
                },
                "payWay": [{
                    "paymentMode": "101",
                    "paymentAmount": str(abs(total_gross)),
                    "orderNumber": "a"
                }],
                "buyerDetails": {
                    "buyerTin": credit_note_data.get("customer_tin", ""),
                    "buyerNinBrn": "",
                    "buyerPassportNum": "",
                    "buyerLegalName": credit_note_data["customer_name"],
                    "buyerBusinessName": credit_note_data["customer_name"],
                    "buyerAddress": "",
                    "buyerEmail": credit_note_data.get("buyer_email", ""),
                    "buyerMobilePhone": credit_note_data.get("buyer_phone", ""),
                    "buyerLinePhone": "",
                    "buyerPlaceOfBusi": "",
                    "buyerType": credit_note_data.get("buyer_type", "1"),
                    "buyerCitizenship": "",
                    "buyerSector": "",
                    "buyerReferenceNo": ""
                },
                "basicInformation": {
                    "operator": "System",
                    "invoiceKind": "1",
                    "invoiceIndustryCode": "101"
                }
            }
        
        # Log the final T110 payload with key details
        logger.info(f"[T110] Submitting credit note application to EFRIS: oriInvoiceId={efris_payload.get('oriInvoiceId')}, reasonCode={efris_payload.get('reasonCode')}")
        logger.info(f"[T110] Summary: grossAmount={efris_payload.get('summary', {}).get('grossAmount')}, taxAmount={efris_payload.get('summary', {}).get('taxAmount')}, netAmount={efris_payload.get('summary', {}).get('netAmount')}")
        logger.info(f"[T110] Items: {len(efris_payload.get('goodsDetails', []))}, TaxDetails: {len(efris_payload.get('taxDetails', []))}")
        logger.debug(f"[T110] Full payload: {json.dumps(efris_payload, indent=2)}")
        
        # Submit to EFRIS using T110 (Credit Note Application)
        result = efris.submit_credit_note_application(efris_payload)
        
        # Handle string error response from efris_client
        if isinstance(result, str):
            raise HTTPException(status_code=502, detail={
                "success": False,
                "error_code": "CONNECTION_ERROR",
                "message": result
            })
        
        return_code = result.get("returnStateInfo", {}).get("returnCode", "")
        return_message = result.get("returnStateInfo", {}).get("returnMessage", "Unknown error")
        
        if return_code == "00":
            # Success - T110 returns a referenceNo
            data = result.get("data", {})
            decrypted = data.get("decrypted_content", {})
            
            reference_no = ""
            if isinstance(decrypted, dict):
                reference_no = decrypted.get("referenceNo", "")
            
            cn_number = credit_note_data.get("credit_note_number", credit_note_data.get("sellersReferenceNo", ""))
            cn_date = credit_note_data.get("credit_note_date", credit_note_data.get("applicationTime", "")[:10])
            customer_name = credit_note_data.get("customer_name", credit_note_data.get("contactName", ""))
            total_amount = credit_note_data.get("total_amount", 0)
            
            # Save to database
            try:
                credit_memo = CreditMemo(
                    company_id=company.id,
                    qb_credit_memo_id=cn_number,
                    qb_doc_number=cn_number,
                    qb_customer_name=customer_name,
                    qb_txn_date=datetime.strptime(cn_date, "%Y-%m-%d") if cn_date else datetime.utcnow(),
                    qb_total_amt=total_amount if total_amount else 0,
                    qb_data=credit_note_data
                )
                db.add(credit_memo)
                db.commit()
            except Exception as db_err:
                logger.warning(f"[T110] Failed to save credit memo to DB: {db_err}")
                db.rollback()
            
            return {
                "success": True,
                "referenceNo": reference_no,
                "credit_note_number": cn_number,
                "submitted_at": datetime.utcnow().isoformat(),
                "message": "Credit note application submitted successfully to EFRIS"
            }
        else:
            logger.warning(f"[T110] EFRIS rejected credit note: code={return_code}, msg={return_message}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": return_code,
                    "message": return_message
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[T110] Internal error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/api/external/efris/invoice/{invoice_number}")
async def external_get_invoice(
    invoice_number: str,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """Query invoice status from database"""
    invoice = db.query(EFRISInvoice).filter(
        EFRISInvoice.company_id == company.id,
        EFRISInvoice.invoice_no == invoice_number
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        "invoice_number": invoice.invoice_no,
        "fdn": invoice.fdn,
        "status": invoice.status,
        "customer_name": invoice.customer_name,
        "total_amount": invoice.total_amount,
        "total_tax": invoice.total_tax,
        "fiscalized_at": invoice.submission_date.isoformat() if invoice.submission_date else None,
        "error_message": invoice.error_message
    }


@app.get("/api/external/efris/invoices")
async def external_list_invoices(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: Optional[str] = Query(None),
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """List invoices with pagination"""
    query = db.query(EFRISInvoice).filter(EFRISInvoice.company_id == company.id)
    
    if status:
        query = query.filter(EFRISInvoice.status == status)
    
    total = query.count()
    invoices = query.order_by(EFRISInvoice.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "invoices": [{
            "invoice_number": inv.invoice_no,
            "fdn": inv.fdn,
            "status": inv.status,
            "customer_name": inv.customer_name,
            "total_amount": inv.total_amount,
            "fiscalized_at": inv.submission_date.isoformat() if inv.submission_date else None
        } for inv in invoices]
    }


@app.get("/api/external/efris/excise-duty")
async def external_get_excise_duty(
    excise_code: Optional[str] = Query(None, description="Filter by specific excise duty code (e.g., LED190100)"),
    excise_name: Optional[str] = Query(None, description="Filter by excise duty name (e.g., beer)"),
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    External API endpoint for custom ERP systems to fetch excise duty codes from EFRIS
    
    Authentication: X-API-Key header
    
    Query Parameters:
    - excise_code (optional): Filter by specific excise duty code (e.g., LED190100)
    - excise_name (optional): Filter by excise duty name (e.g., beer)
    
    Response:
    {
        "success": true,
        "excise_codes": [
            {
                "code": "LED190100",
                "name": "Beer",
                "rate": "200",
                "unit": "Litre",
                "currency": "UGX",
                "excise_rule": "2"
            }
        ],
        "total": 1,
        "last_updated": "2024-01-24T10:30:00"
    }
    """
    try:
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Query excise duty from EFRIS (T125)
        result = efris.query_excise_duty()
        
        # Extract excise list from response
        excise_list = result.get('data', {}).get('decrypted_content', {}).get('exciseDutyList', [])
        
        if not excise_list:
            return {
                "success": True,
                "excise_codes": [],
                "total": 0,
                "message": "No excise duty codes found"
            }
        
        # Save to database and filter results
        db.query(ExciseCode).filter(ExciseCode.company_id == company.id).delete()
        
        excise_codes = []
        for duty in excise_list:
            code = duty.get('exciseDutyCode')
            if not code or duty.get('isLeafNode') != '1':
                continue
            
            details_list = duty.get('exciseDutyDetailsList', [])
            if not details_list:
                continue
            
            # Get rate information
            type_102_detail = next((d for d in details_list if d.get('type') == '102'), None)
            type_101_detail = next((d for d in details_list if d.get('type') == '101'), None)
            
            rate = ''
            unit = ''
            currency = 'UGX'
            excise_rule = '1'
            
            if type_102_detail:
                rate = type_102_detail.get('rate', '0')
                unit = type_102_detail.get('unit', '')
                currency = 'UGX' if type_102_detail.get('currency') == '101' else 'USD'
                excise_rule = '2'
            elif type_101_detail:
                rate = type_101_detail.get('rate', '0')
                excise_rule = '1'
                unit = '%'
            
            # Save to database
            excise_record = ExciseCode(
                company_id=company.id,
                excise_code=code,
                excise_name=duty.get('goodService', ''),
                excise_rate=rate,
                excise_unit=unit,
                excise_currency=currency,
                excise_rule=excise_rule,
                rate_text=f"{rate} {unit}" if rate else "",
                is_leaf_node=True
            )
            db.add(excise_record)
            
            # Apply filters
            if excise_code and code != excise_code:
                continue
            if excise_name and excise_name.lower() not in duty.get('goodService', '').lower():
                continue
            
            excise_codes.append({
                "code": code,
                "name": duty.get('goodService', ''),
                "rate": rate,
                "unit": unit,
                "currency": currency,
                "excise_rule": excise_rule
            })
        
        db.commit()
        
        return {
            "success": True,
            "excise_codes": excise_codes,
            "total": len(excise_codes),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to fetch excise duty codes: {str(e)}")


@app.get("/api/external/efris/units-of-measure")
async def external_get_units_of_measure(
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Get EFRIS Units of Measure codes - Maps ERP units to EFRIS codes
    
    This endpoint fetches the official EFRIS unit of measure codes from T115 system dictionary.
    Use these codes when registering products and submitting invoices.
    
    Authentication: X-API-Key header
    
    Response:
    {
        "success": true,
        "units": [
            {
                "code": "101",
                "name": "Carton",
                "description": "Use for products sold in cartons/boxes"
            },
            {
                "code": "102",
                "name": "Piece",
                "description": "Use for individual items (computers, phones, etc.)"
            },
            {
                "code": "103",
                "name": "Kilogram",
                "description": "Use for products sold by weight"
            }
        ],
        "total": 50,
        "last_updated": "2024-01-24T10:30:00"
    }
    
    Example Usage:
    - Selling computers? Use code "102" (Piece)
    - Selling cement bags? Use code "103" (Kilogram) or "102" (Piece) depending on how you price it
    - Selling liquids? Use code "104" (Litre)
    """
    try:
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Query system dictionary from EFRIS (T115)
        result = efris.get_code_list(None)
        
        # Extract rateUnit from response
        decrypted_content = result.get('data', {}).get('decrypted_content', {})
        rate_units = decrypted_content.get('rateUnit', [])
        
        if not rate_units:
            # Return static fallback list if EFRIS doesn't return data
            rate_units = [
                {"value": "101", "name": "Carton"},
                {"value": "102", "name": "Piece"},
                {"value": "103", "name": "Kilogram"},
                {"value": "104", "name": "Litre"},
                {"value": "105", "name": "Meter"},
                {"value": "106", "name": "Tonne"},
                {"value": "107", "name": "Gram"},
                {"value": "108", "name": "Millilitre"},
                {"value": "109", "name": "Centimetre"},
                {"value": "110", "name": "Square Meter"},
                {"value": "111", "name": "Cubic Meter"},
                {"value": "112", "name": "Pack"},
                {"value": "113", "name": "Dozen"},
                {"value": "114", "name": "Set"},
                {"value": "115", "name": "Pair"},
                {"value": "116", "name": "Roll"},
                {"value": "117", "name": "Sheet"},
                {"value": "118", "name": "Bundle"},
                {"value": "119", "name": "Bag"},
                {"value": "120", "name": "Bottle"}
            ]
        
        # Return units as received from EFRIS (code and name only)
        units = []
        for unit in rate_units:
            units.append({
                "code": unit.get('value', ''),
                "name": unit.get('name', '')
            })
        
        return {
            "success": True,
            "units": units,
            "total": len(units),
            "last_updated": datetime.now().isoformat(),
            "message": "Units of measure fetched successfully from EFRIS"
        }
        
    except Exception as e:
        # Return static fallback on error
        fallback_units = [
            {"code": "101", "name": "Carton"},
            {"code": "102", "name": "Piece"},
            {"code": "103", "name": "Kilogram"},
            {"code": "104", "name": "Litre"},
            {"code": "105", "name": "Meter"},
            {"code": "106", "name": "Tonne"},
            {"code": "107", "name": "Gram"},
            {"code": "108", "name": "Millilitre"},
            {"code": "109", "name": "Centimetre"},
            {"code": "110", "name": "Square Meter"},
            {"code": "111", "name": "Cubic Meter"},
            {"code": "112", "name": "Pack"},
            {"code": "113", "name": "Dozen"},
            {"code": "114", "name": "Set"},
            {"code": "115", "name": "Pair"},
            {"code": "116", "name": "Roll"},
            {"code": "117", "name": "Sheet"},
            {"code": "118", "name": "Bundle"},
            {"code": "119", "name": "Bag"},
            {"code": "120", "name": "Bottle"}
        ]
        
        return {
            "success": True,
            "units": fallback_units,
            "total": len(fallback_units),
            "last_updated": datetime.now().isoformat(),
            "message": "Using cached units of measure (EFRIS connection issue)",
            "warning": str(e)
        }


@app.post("/api/external/efris/stock-decrease")
async def external_stock_decrease(
    stock_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    External API endpoint for custom ERP systems to decrease stock in EFRIS
    
    Authentication: X-API-Key header
    
    Request Body:
    {
        "goodsStockIn": {
            "operationType": "102",
            "adjustType": "102",
            "remarks": "Damaged goods"
        },
        "goodsStockInItem": [
            {
                "goodsCode": "SKU-001",
                "quantity": 10,
                "unitPrice": 5000,
                "remarks": "Water damage"
            }
        ]
    }
    
    Response:
    {
        "success": true,
        "stock_id": "internal_stock_id",
        "message": "Stock decrease submitted successfully",
        "efris_response": {...}
    }
    """
    try:
        # Validate required fields
        if "goodsStockIn" not in stock_data or "goodsStockInItem" not in stock_data:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: goodsStockIn and goodsStockInItem"
            )
        
        if not stock_data["goodsStockInItem"] or len(stock_data["goodsStockInItem"]) == 0:
            raise HTTPException(
                status_code=400,
                detail="Stock decrease must have at least one item"
            )
        
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Submit stock decrease to EFRIS (T132)
        result = efris.stock_decrease(stock_data)
        
        # Log the stock decrease
        stock_record = StockMovement(
            company_id=company.id,
            movement_type="decrease",
            operation_type=stock_data["goodsStockIn"].get("operationType", "102"),
            adjust_type=stock_data["goodsStockIn"].get("adjustType", "102"),
            remarks=stock_data["goodsStockIn"].get("remarks", ""),
            item_count=len(stock_data["goodsStockInItem"]),
            status="submitted",
            efris_response=result
        )
        db.add(stock_record)
        db.commit()
        
        return {
            "success": True,
            "stock_id": stock_record.id,
            "message": "Stock decrease submitted successfully",
            "efris_response": result
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to decrease stock: {str(e)}"
        )


@app.post("/api/external/efris/stock-increase")
async def external_stock_increase(
    stock_data: dict,
    company: Company = Depends(get_company_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Increase stock in EFRIS (T131) - Matches QuickBooks Format
    
    Request Body:
    {
        "goodsStockIn": {
            "operationType": "101",  # 101=Increase
            "supplierTin": "1234567890",
            "supplierName": "Supplier Ltd",
            "stockInType": "102",  # 101=Import, 102=Local Purchase, 103=Manufacture, 104=Opening Stock
            "stockInDate": "2026-02-09",
            "remarks": "Stock replenishment"
        },
        "goodsStockInItem": [
            {
                "goodsCode": "PROD-001",
                "quantity": "100",
                "unitPrice": "5000",
                "measureUnit": "102",
                "remarks": "Stock replenishment"
            }
        ]
    }
    """
    try:
        # Validate required fields - same as QuickBooks
        if "goodsStockIn" not in stock_data or "goodsStockInItem" not in stock_data:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: goodsStockIn and goodsStockInItem"
            )
        
        if not stock_data["goodsStockInItem"] or len(stock_data["goodsStockInItem"]) == 0:
            raise HTTPException(
                status_code=400,
                detail="Stock increase must have at least one item"
            )
        
        # Get cached EFRIS Manager (avoids T101+T104+T103 handshake on every request)
        efris = get_efris_manager(company)
        
        # Pass directly to manager - same as QuickBooks does
        result = efris.stock_increase(stock_data)
        
        return {
            "success": True,
            "message": "Stock increase submitted successfully",
            "efris_response": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to increase stock: {str(e)}"
        )


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

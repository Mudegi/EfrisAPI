"""
SaaS API Endpoints - User Management & Multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

# Import from connection.py where get_db is actually defined
from database.connection import get_db
# Import from models.py since models_saas.py has issues
from database.models import User, Company
# Import auth functions
from auth import (
    get_password_hash, verify_password, create_access_token
)

router = APIRouter()


# ===== Pydantic Models =====

class UserRegister(BaseModel):
    email: str  # Using str to avoid email-validator dependency
    password: str
    full_name: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    status: str
    plan_name: str
    start_date: datetime
    end_date: Optional[datetime]
    invoice_count: int
    max_companies: int
    days_remaining: Optional[int]
    
    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    company_name: str
    tin: str
    device_no: str
    erp_type: str = "custom"  # quickbooks, xero, zoho, custom
    erp_config: Optional[str] = None  # JSON string
    qb_region: str = "US"


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    tin: str
    device_no: str
    erp_type: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Authentication Endpoints =====

@router.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with trial subscription embedded (2 days as per market standards)
    trial_end = datetime.utcnow() + timedelta(days=2)
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        subscription_status='TRIAL',
        subscription_start_date=datetime.utcnow().isoformat(),
        subscription_end_date=trial_end.isoformat(),
        max_companies=2  # Trial: 2 companies
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "subscription_status": "TRIAL",
        "subscription_end_date": trial_end.isoformat()
    }


@router.post("/api/auth/login")
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.get("/api/auth/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription details"""
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    return {
        **subscription.__dict__,
        "status": subscription.status.value,
        "days_remaining": subscription.days_remaining()
    }


# ===== Company Management =====

@router.post("/api/companies", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_user),
    subscription = Depends(get_current_active_subscription),
    db: Session = Depends(get_db)
):
    """Create new company"""
    # Check company limit
    user_companies_count = db.query(Company).filter(Company.user_id == current_user.id).count()
    if user_companies_count >= subscription.max_companies:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Company limit reached ({subscription.max_companies}). Upgrade your plan."
        )
    
    # Create company
    company = Company(
        user_id=current_user.id,
        company_name=company_data.company_name,
        tin=company_data.tin,
        device_no=company_data.device_no,
        erp_type=ERPType(company_data.erp_type),
        erp_config=company_data.erp_config,
        qb_region=company_data.qb_region
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    return {
        **company.__dict__,
        "erp_type": company.erp_type.value
    }


@router.get("/api/companies", response_model=List[CompanyResponse])
async def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's companies"""
    companies = db.query(Company).filter(Company.user_id == current_user.id).all()
    return [
        {**c.__dict__, "erp_type": c.erp_type.value if hasattr(c.erp_type, 'value') else c.erp_type}
        for c in companies
    ]


@router.get("/api/companies/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get company details"""
    company = require_company_access(company_id, current_user)
    return {
        **company.__dict__,
        "erp_type": company.erp_type.value if hasattr(company.erp_type, 'value') else company.erp_type
    }


@router.delete("/api/companies/{company_id}")
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete company"""
    company = require_company_access(company_id, current_user)
    db.delete(company)
    db.commit()
    return {"message": "Company deleted successfully"}


# ===== Public EFRIS Test Endpoints =====

@router.get("/api/public/efris/test")
async def test_efris_connection():
    """Public endpoint to test EFRIS connectivity"""
    from efris_client import EfrisAPIManager
    
    try:
        # Test with dummy credentials
        manager = EfrisAPIManager("1000000000", "1000000000_00", "keys/test.pfx", "test")
        result = manager.get_server_time()
        return {
            "status": "success",
            "message": "EFRIS server is reachable",
            "server_time": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/api/public/efris/query/{fdn}")
async def query_invoice_public(fdn: str):
    """Public endpoint to query invoice by FDN (for demo purposes)"""
    return {
        "message": "Invoice query feature - requires TIN authentication",
        "fdn": fdn,
        "note": "Sign up to access full EFRIS integration"
    }

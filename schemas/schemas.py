"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== AUTH SCHEMAS ==========

class UserCreate(BaseModel):
    email: str  # Using str to avoid email-validator dependency
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "reseller"  # reseller or client


class UserLogin(BaseModel):
    email: str  # Using str to avoid email-validator dependency
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional['UserResponse'] = None


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(BaseModel):
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

    class Config:
        from_attributes = True


# ========== CLIENT SCHEMAS (for reseller to manage clients) ==========

class ClientCreate(BaseModel):
    """Schema for reseller to add a new client"""
    company_name: str
    email: str  # Using str to avoid email-validator dependency
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    tin: str
    device_no: str
    cert_password: str
    test_mode: bool = True


class ClientResponse(BaseModel):
    """Response when listing clients"""
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str] = None
    company_name: Optional[str] = None
    tin: Optional[str] = None
    device_no: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ========== COMPANY SCHEMAS ==========

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
    erp_type: Optional[str] = None  # Allow changing ERP: QUICKBOOKS, XERO, ZOHO, CUSTOM
    erp_config: Optional[dict] = None  # ERP-specific configuration (realm_id, tenant_id, etc.)


class CompanyResponse(BaseModel):
    id: int
    name: str
    tin: str
    device_no: Optional[str]
    efris_test_mode: bool
    qb_company_name: Optional[str]
    is_active: bool
    created_at: datetime
    erp_type: Optional[str] = None  # Current ERP system
    erp_config: Optional[dict] = None  # ERP-specific config

    class Config:
        from_attributes = True


class CompanyWithRole(CompanyResponse):
    role: str


# ========== PRODUCT SCHEMAS ==========

class ProductCreate(BaseModel):
    qb_item_id: str
    qb_name: str
    qb_sku: Optional[str] = None
    qb_description: Optional[str] = None
    qb_unit_price: Optional[float] = None
    efris_product_code: Optional[str] = None
    efris_commodity_code: Optional[str] = None
    efris_unit_of_measure: str = "101"
    has_excise: bool = False
    excise_duty_code: Optional[str] = None


class ProductResponse(BaseModel):
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

    class Config:
        from_attributes = True


# ========== INVOICE SCHEMAS ==========

class InvoiceCreate(BaseModel):
    qb_invoice_id: str
    qb_doc_number: str
    qb_customer_name: str
    qb_total_amt: float
    qb_data: dict


class InvoiceResponse(BaseModel):
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

    class Config:
        from_attributes = True


# ========== COMPANY USER SCHEMAS ==========

class CompanyUserAdd(BaseModel):
    email: str  # Using str to avoid email-validator dependency
    role: str = Field(default="user", pattern="^(admin|user|readonly)$")


class CompanyUserResponse(BaseModel):
    user_id: int
    user_email: str
    user_name: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

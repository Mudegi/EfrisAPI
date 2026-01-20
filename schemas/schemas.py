"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== AUTH SCHEMAS ==========

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
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


class CompanyResponse(BaseModel):
    id: int
    name: str
    tin: str
    device_no: Optional[str]
    efris_test_mode: bool
    qb_company_name: Optional[str]
    is_active: bool
    created_at: datetime

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
    email: EmailStr
    role: str = Field(default="user", pattern="^(admin|user|readonly)$")


class CompanyUserResponse(BaseModel):
    user_id: int
    user_email: str
    user_name: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

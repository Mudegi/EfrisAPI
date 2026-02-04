"""
SaaS Multi-tenant Models
Users → Companies → Subscriptions → ERPs
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

# Import Base from models.py where it's defined
try:
    from .models import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class SubscriptionStatus(enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ERPType(enum.Enum):
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    ZOHO = "zoho"
    CUSTOM = "custom"


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # Hashed password
    full_name = Column(String, nullable=False)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    companies = relationship("Company", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    plan_name = Column(String, default="Annual")  # Annual, Trial, etc.
    amount_paid = Column(Float, default=0.0)
    currency = Column(String, default="UGX")
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)  # Subscription expiry
    invoice_count = Column(Integer, default=0)  # Track usage
    max_companies = Column(Integer, default=5)  # Limit per plan
    
    # Payment tracking
    last_payment_date = Column(DateTime)
    last_payment_amount = Column(Float)
    payment_reference = Column(String)  # Transaction ref
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def is_valid(self):
        """Check if subscription is active and not expired"""
        if self.status == SubscriptionStatus.CANCELLED:
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]
    
    def days_remaining(self):
        """Days until subscription expires"""
        if not self.end_date:
            return None
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)


class Company(Base):
    """Updated Company model with user relationship and ERP config"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Company basics
    company_name = Column(String, nullable=False)
    tin = Column(String, nullable=False, index=True)
    device_no = Column(String, nullable=False)
    certificate_path = Column(String)  # Path to .pfx file
    certificate_password = Column(String)  # Encrypted
    
    # ERP Configuration
    erp_type = Column(Enum(ERPType), default=ERPType.CUSTOM)
    erp_config = Column(Text)  # JSON config for ERP (tokens, credentials, etc.)
    
    # Settings
    qb_region = Column(String, default='US')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="companies")
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    invoices = relationship("EFRISInvoice", back_populates="company", cascade="all, delete-orphan")


class Product(Base):
    """Product catalog per company"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # Product details
    qb_id = Column(String, index=True)  # ERP product ID
    qb_name = Column(String, nullable=False)
    description = Column(String)
    
    # EFRIS metadata
    commodity_code = Column(String)  # EFRIS commodity category
    unit_of_measure = Column(String, default='101')
    
    # Tax configuration
    is_exempt = Column(Boolean, default=False)
    is_zero_rated = Column(Boolean, default=False)
    tax_rate = Column(Float, default=0.18)
    
    # Excise duty
    has_excise = Column(Boolean, default=False)
    excise_duty_code = Column(String)
    excise_rate = Column(String)
    excise_unit = Column(String)
    excise_rule = Column(String, default='2')
    
    # Relationships
    company = relationship("Company", back_populates="products")


class EFRISInvoice(Base):
    """Track fiscalized invoices"""
    __tablename__ = 'efris_invoices'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # ERP reference
    erp_invoice_id = Column(String, index=True)  # ID from ERP system
    erp_invoice_number = Column(String)  # Display number
    
    # EFRIS response
    fdn = Column(String, unique=True, index=True)
    invoice_no = Column(String)
    antifake_code = Column(String)
    qr_code_url = Column(String)
    
    # Invoice data
    customer_name = Column(String)
    total_amount = Column(Float)
    tax_amount = Column(Float)
    invoice_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    fiscalized_at = Column(DateTime)
    
    # Relationships
    company = relationship("Company", back_populates="invoices")


class AuditLog(Base):
    """Track all API operations for security and billing"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)
    
    action = Column(String, nullable=False)  # 'invoice_fiscalized', 'login', 'product_registered'
    endpoint = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    
    request_data = Column(Text)  # JSON
    response_data = Column(Text)  # JSON
    
    success = Column(Boolean, default=True)
    error_message = Column(String)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

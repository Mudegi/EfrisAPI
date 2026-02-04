"""
Database Models for Multi-Tenant EFRIS API
Supports: Admin → Resellers → Clients (Taxpayers)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"           # Platform owner (you)
    RESELLER = "reseller"     # Agents/accountants who bring clients
    CLIENT = "client"         # End taxpayer who uses control panel


class UserStatus(enum.Enum):
    """User account status (for activation workflow)"""
    PENDING = "pending"       # Waiting for owner approval
    ACTIVE = "active"         # Approved and active
    SUSPENDED = "suspended"   # Temporarily disabled
    DEACTIVATED = "deactivated"  # Permanently disabled


class SubscriptionStatus(enum.Enum):
    """Subscription status for resellers"""
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class User(Base):
    """
    User accounts - supports different roles:
    - ADMIN: Platform owner
    - RESELLER: Agents who register, pay, and manage clients
    - CLIENT: End taxpayers who use the control panel
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    role = Column(String(20), default="client")  # admin, reseller, client, owner
    status = Column(String(20), default="active")  # pending, active, suspended, deactivated
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # For RESELLER: who manages this reseller (admin)
    # For CLIENT: who manages this client (reseller_id)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Subscription (for resellers)
    subscription_status = Column(String(20), default="trial")  # trial, active, expired
    subscription_ends = Column(DateTime(timezone=True))
    max_clients = Column(Integer, default=5)  # How many clients can reseller add
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company_users = relationship("CompanyUser", back_populates="user")
    # For resellers: their clients
    clients = relationship("User", backref="reseller", remote_side=[id])


class Company(Base):
    """
    Company/Business - stores EFRIS credentials for each taxpayer
    Each CLIENT has ONE company with their TIN, device_no, and private key
    """
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tin = Column(String(50), unique=True, index=True, nullable=False)
    device_no = Column(String(50))
    
    # Owner - the CLIENT user who owns this company
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # EFRIS Configuration (CRITICAL - stored by reseller for the client)
    efris_test_mode = Column(Boolean, default=True)
    efris_cert_path = Column(String(500))      # Path to .pfx file
    efris_cert_password = Column(String(255))  # Password for .pfx
    efris_aes_key = Column(Text)               # Cached AES key
    efris_aes_key_expires = Column(DateTime(timezone=True))
    
    # QuickBooks Configuration (optional - if client uses QB)
    qb_realm_id = Column(String(50))
    qb_access_token = Column(Text)
    qb_refresh_token = Column(Text)
    qb_token_expires = Column(DateTime(timezone=True))
    qb_company_name = Column(String(255))
    qb_region = Column(String(10), default="US")
    
    # Xero Configuration (optional - if client uses Xero)
    xero_tenant_id = Column(String(100))
    xero_access_token = Column(Text)
    xero_refresh_token = Column(Text)
    xero_token_expires = Column(DateTime(timezone=True))
    
    # Zoho Books Configuration (optional)
    zoho_organization_id = Column(String(100))
    zoho_access_token = Column(Text)
    zoho_refresh_token = Column(Text)
    zoho_token_expires = Column(DateTime(timezone=True))
    
    # Custom ERP/API Configuration (optional)
    custom_api_url = Column(String(500))
    custom_api_key = Column(Text)
    custom_api_secret = Column(Text)
    
    # ERP Connection Status
    erp_type = Column(String(50))  # quickbooks, xero, zoho, custom, none
    erp_connected = Column(Boolean, default=False)
    erp_last_sync = Column(DateTime(timezone=True))
    
    # API Access for Custom ERP Integration
    api_key = Column(String(100), unique=True, index=True)  # For external API calls
    api_secret = Column(String(100))  # Optional signing secret
    api_enabled = Column(Boolean, default=True)
    api_last_used = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    company_users = relationship("CompanyUser", back_populates="company")
    products = relationship("Product", back_populates="company")
    invoices = relationship("Invoice", back_populates="company")
    purchase_orders = relationship("PurchaseOrder", back_populates="company")


class CompanyUser(Base):
    """Many-to-many relationship between users and companies with roles"""
    __tablename__ = "company_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    role = Column(String(50), default="user")  # admin, user, readonly
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="company_users")
    company = relationship("Company", back_populates="company_users")


class ClientReferral(Base):
    """
    Client referrals from resellers - OWNER MUST APPROVE
    Security: Prevents resellers from adding/deleting clients directly
    """
    __tablename__ = "client_referrals"

    id = Column(Integer, primary_key=True, index=True)
    
    # Referral Info
    reseller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=False)
    client_phone = Column(String(50))
    tin = Column(String(50), nullable=False)
    device_no = Column(String(50))
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, rejected
    notes = Column(Text)  # Reseller's notes about the client
    
    # Owner's Actions
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Owner who reviewed
    reviewed_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # When approved, links to created client
    created_client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reseller = relationship("User", foreign_keys=[reseller_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    created_client = relationship("User", foreign_keys=[created_client_id])
    created_company = relationship("Company", foreign_keys=[created_company_id])


class Product(Base):
    """Products cached from QuickBooks with EFRIS metadata"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # QuickBooks Data
    qb_item_id = Column(String(50), nullable=False, index=True)
    qb_name = Column(String(255))
    qb_sku = Column(String(100))
    qb_description = Column(Text)
    qb_unit_price = Column(Float)
    qb_type = Column(String(50))  # Inventory, Service, etc.
    
    # EFRIS Metadata
    efris_product_code = Column(String(100))  # itemCode for EFRIS
    efris_commodity_code = Column(String(100))  # goodsCategoryId
    efris_unit_of_measure = Column(String(10))
    efris_status = Column(String(50), default="Pending Registration")  # Registered, Pending Registration
    efris_id = Column(String(50))  # EFRIS system ID
    
    # Excise Duty
    has_excise = Column(Boolean, default=False)
    excise_duty_code = Column(String(50))
    excise_unit = Column(String(10))
    excise_rate = Column(String(50))
    excise_rule = Column(String(10))
    
    # Tax Classification
    is_zero_rated = Column(Boolean, default=False)  # 0% VAT
    is_exempt = Column(Boolean, default=False)  # Tax exempt
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    synced_at = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="products")


class Invoice(Base):
    """Invoices from QuickBooks with EFRIS fiscalization data"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # QuickBooks Data
    qb_invoice_id = Column(String(50), nullable=False, index=True)
    qb_doc_number = Column(String(100))
    qb_customer_name = Column(String(255))
    qb_txn_date = Column(DateTime)
    qb_total_amt = Column(Float)
    qb_data = Column(JSON)  # Full QB invoice data
    
    # EFRIS Fiscalization
    efris_fdn = Column(String(100), unique=True, index=True)  # Fiscal Document Number
    efris_verification_code = Column(String(100))
    efris_qr_code = Column(Text)
    efris_invoice_id = Column(String(100))
    efris_status = Column(String(50), default="Pending")  # Fiscalized, Pending, Failed
    efris_response = Column(JSON)  # Full EFRIS response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    fiscalized_at = Column(DateTime(timezone=True))

    # Relationships
    company = relationship("Company", back_populates="invoices")


class PurchaseOrder(Base):
    """Purchase Orders from QuickBooks"""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # QuickBooks Data
    qb_po_id = Column(String(50), nullable=False, index=True)
    qb_doc_number = Column(String(100))
    qb_vendor_name = Column(String(255))
    qb_txn_date = Column(DateTime)
    qb_total_amt = Column(Float)
    qb_data = Column(JSON)  # Full QB PO data
    
    # EFRIS Status
    efris_status = Column(String(50), default="pending")  # pending, sent, failed
    efris_sent_at = Column(DateTime(timezone=True))  # When sent to EFRIS
    efris_response = Column(JSON)  # EFRIS response data
    efris_error = Column(Text)  # Error message if failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="purchase_orders")


class CreditMemo(Base):
    """Credit Memos from QuickBooks"""
    __tablename__ = "credit_memos"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # QuickBooks Data
    qb_credit_memo_id = Column(String(50), nullable=False, index=True)
    qb_doc_number = Column(String(100))
    qb_customer_name = Column(String(255))
    qb_txn_date = Column(DateTime)
    qb_total_amt = Column(Float)
    qb_data = Column(JSON)  # Full QB credit memo data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EFRISGood(Base):
    """Goods/Products imported from EFRIS"""
    __tablename__ = "efris_goods"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # EFRIS Data
    goods_code = Column(String(100), index=True)  # goodsCode
    goods_name = Column(String(255))  # goodsName
    commodity_category_code = Column(String(100))  # commodityCategoryCode
    commodity_category_name = Column(String(255))  # commodityCategoryName
    unit_price = Column(Float)  # unitPrice
    currency = Column(String(10))  # currency
    tax_rate = Column(Float)  # taxRate (as decimal, e.g., 0.18)
    have_excise_tax = Column(String(10))  # haveExciseTax
    stock = Column(Float)  # stock
    
    # Full data
    efris_data = Column(JSON)  # Complete EFRIS response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    imported_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company")


class EFRISInvoice(Base):
    """Invoices imported from EFRIS and submitted to EFRIS"""
    __tablename__ = "efris_invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # QuickBooks Reference (for outgoing invoices)
    qb_invoice_id = Column(String(100), index=True)  # QuickBooks invoice ID
    qb_invoice_number = Column(String(100))  # QuickBooks DocNumber
    invoice_date = Column(Date)  # Invoice date
    customer_name = Column(String(255))  # Customer name
    customer_tin = Column(String(50))  # Customer TIN
    buyer_type = Column(String(10))  # 0=Business, 1=Individual, etc.
    total_amount = Column(Float)  # Total invoice amount
    total_tax = Column(Float)  # Total VAT
    total_excise = Column(Float)  # Total excise duty
    total_discount = Column(Float)  # Total discount
    
    # Submission Status (for outgoing invoices)
    status = Column(String(50))  # draft, pending, submitted, success, failed
    fdn = Column(String(100))  # Fiscal Document Number from EFRIS
    efris_invoice_id = Column(String(100))  # EFRIS invoice ID
    submission_date = Column(DateTime)  # When submitted
    error_message = Column(Text)  # Error details if failed
    efris_payload = Column(JSON)  # T109 request payload
    efris_response = Column(JSON)  # T109 response
    
    # EFRIS Data (for imported invoices)
    invoice_no = Column(String(100), index=True)  # invoiceNo
    invoice_kind = Column(String(10))  # invoiceKind
    invoice_type = Column(String(10))  # invoiceType
    invoice_industry_code = Column(String(100))  # invoiceIndustryCode
    
    # Buyer Info (for imported invoices)
    buyer_legal_name = Column(String(255))  # buyerLegalName
    buyer_business_name = Column(String(255))  # buyerBusinessName
    buyer_tin = Column(String(50))  # buyerTin (if available)
    
    # Amounts (for imported invoices)
    currency = Column(String(10))  # currency
    gross_amount = Column(Float)  # grossAmount
    tax_amount = Column(Float)  # taxAmount
    net_amount = Column(Float)  # netAmount
    
    # Dates (for imported invoices)
    issued_date_str = Column(String(50))  # issuedDateStr
    issued_date = Column(DateTime)  # parsed from issuedDate
    uploading_time = Column(String(50))  # uploadingTime
    
    # Status (for imported invoices)
    is_invalid = Column(String(10))  # isInvalid
    is_refund = Column(String(10))  # isRefund
    
    # Reference
    reference_no = Column(String(100))  # referenceNo
    device_no = Column(String(100))  # deviceNo
    
    # Full data
    efris_data = Column(JSON)  # Complete EFRIS response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    imported_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company")


class ExciseCode(Base):
    """Excise duty codes from EFRIS T125 - stored per company"""
    __tablename__ = "excise_codes"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Excise code data
    excise_code = Column(String(50), nullable=False, index=True)  # e.g., LED190400
    excise_name = Column(Text)  # goodService description
    excise_rate = Column(String(50))  # Rate value
    excise_unit = Column(String(10))  # Unit code (101, 102, etc.)
    excise_currency = Column(String(10))  # Currency code
    excise_rule = Column(String(10))  # 1=percentage, 2=fixed rate
    rate_text = Column(String(255))  # Formatted rate text for display
    is_leaf_node = Column(Boolean, default=True)  # Only leaf nodes are selectable
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """Audit trail for all operations"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))  # Product, Invoice, etc.
    resource_id = Column(String(50))
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ActivityLog(Base):
    """Activity log for tracking invoice/EFRIS operations (for owner dashboard)"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))  # The client user
    reseller_id = Column(Integer, ForeignKey("users.id"))  # The reseller who manages this client
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # invoice_created, invoice_fiscalized, product_synced, etc.
    document_type = Column(String(50))  # invoice, credit_memo, product
    document_number = Column(String(100))  # INV-1023, etc.
    
    # EFRIS specific
    efris_request_type = Column(String(20))  # T109, T110, T111, etc.
    efris_status = Column(String(20))  # success, failed, pending
    efris_response = Column(JSON)  # Store EFRIS response
    
    # Metadata
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company")
    user = relationship("User", foreign_keys=[user_id])
    reseller = relationship("User", foreign_keys=[reseller_id])

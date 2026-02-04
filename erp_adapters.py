"""
ERP Adapter Pattern - Support multiple ERP systems
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import json


class ERPAdapter(ABC):
    """Base class for all ERP integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with ERP system"""
        pass
    
    @abstractmethod
    async def get_invoices(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Fetch invoices from ERP"""
        pass
    
    @abstractmethod
    async def get_invoice(self, invoice_id: str) -> Dict:
        """Get single invoice by ID"""
        pass
    
    @abstractmethod
    async def get_products(self) -> List[Dict]:
        """Fetch products/items from ERP"""
        pass
    
    @abstractmethod
    async def get_customers(self) -> List[Dict]:
        """Fetch customers from ERP"""
        pass
    
    @abstractmethod
    def transform_to_efris(self, invoice: Dict, company_info: Dict) -> Dict:
        """Transform ERP invoice format to EFRIS format"""
        pass


class QuickBooksAdapter(ERPAdapter):
    """QuickBooks integration - existing logic"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        from quickbooks_client import QuickBooksClient
        self.client = QuickBooksClient()
    
    async def authenticate(self) -> bool:
        return self.client.is_authenticated()
    
    async def get_invoices(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        return self.client.get_invoices(start_date, end_date)
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        return self.client.get_invoice(invoice_id)
    
    async def get_products(self) -> List[Dict]:
        return self.client.get_items()
    
    async def get_customers(self) -> List[Dict]:
        return self.client.get_customers()
    
    def transform_to_efris(self, invoice: Dict, company_info: Dict) -> Dict:
        from quickbooks_efris_mapper import QuickBooksEfrisMapper
        return QuickBooksEfrisMapper.map_invoice_to_efris(invoice, {}, company_info)


class XeroAdapter(ERPAdapter):
    """Xero integration"""
    
    async def authenticate(self) -> bool:
        # TODO: Implement Xero OAuth
        return True
    
    async def get_invoices(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        # TODO: Fetch from Xero API
        return []
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        # TODO: Fetch single invoice
        return {}
    
    async def get_products(self) -> List[Dict]:
        return []
    
    async def get_customers(self) -> List[Dict]:
        return []
    
    def transform_to_efris(self, invoice: Dict, company_info: Dict) -> Dict:
        """Transform Xero invoice to EFRIS format"""
        # Similar structure to QuickBooks mapper
        # TODO: Implement Xero-specific transformation
        return {}


class ZohoAdapter(ERPAdapter):
    """Zoho Books integration"""
    
    async def authenticate(self) -> bool:
        # TODO: Implement Zoho OAuth
        return True
    
    async def get_invoices(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        return []
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        return {}
    
    async def get_products(self) -> List[Dict]:
        return []
    
    async def get_customers(self) -> List[Dict]:
        return []
    
    def transform_to_efris(self, invoice: Dict, company_info: Dict) -> Dict:
        # TODO: Implement Zoho-specific transformation
        return {}


class CustomAPIAdapter(ERPAdapter):
    """Generic adapter for custom/manual API integration"""
    
    async def authenticate(self) -> bool:
        # Custom API key validation
        return bool(self.config.get('api_key'))
    
    async def get_invoices(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        # Users provide invoices via API directly
        return []
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        return {}
    
    async def get_products(self) -> List[Dict]:
        return []
    
    async def get_customers(self) -> List[Dict]:
        return []
    
    def transform_to_efris(self, invoice: Dict, company_info: Dict) -> Dict:
        """Expect invoice already in EFRIS-compatible format"""
        # Minimal transformation - validate required fields
        return invoice


def get_erp_adapter(erp_type: str, config: Dict[str, Any]) -> ERPAdapter:
    """Factory to create appropriate ERP adapter"""
    adapters = {
        "quickbooks": QuickBooksAdapter,
        "xero": XeroAdapter,
        "zoho": ZohoAdapter,
        "custom": CustomAPIAdapter,
    }
    
    adapter_class = adapters.get(erp_type.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported ERP type: {erp_type}")
    
    return adapter_class(config)

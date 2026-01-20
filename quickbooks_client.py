"""
QuickBooks Online API Client
Handles OAuth authentication and data fetching from QuickBooks
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urlencode

class QuickBooksClient:
    """QuickBooks Online API Client"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, environment: str = "sandbox"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.environment = environment
        
        # Set base URLs based on environment
        if environment == "production":
            self.base_url = "https://quickbooks.api.intuit.com"
            self.authorization_endpoint = "https://appcenter.intuit.com/connect/oauth2"
        else:
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
            self.authorization_endpoint = "https://appcenter.intuit.com/connect/oauth2"
        
        # OAuth URLs (same for both environments)
        self.token_endpoint = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.revoke_endpoint = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.realm_id: Optional[str] = None  # QuickBooks Company ID
        self.token_expiry: Optional[datetime] = None
        
    def get_authorization_url(self, state: str = "security_token") -> str:
        """Generate OAuth authorization URL for user to grant access"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'com.intuit.quickbooks.accounting',
            'state': state
        }
        return f"{self.authorization_endpoint}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(
            self.token_endpoint,
            headers=headers,
            data=data,
            auth=(self.client_id, self.client_secret)
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
            return token_data
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def refresh_access_token(self) -> Dict:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise Exception("No refresh token available. Please re-authenticate.")
            
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(
                self.token_endpoint,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
                print(f"[QB] Token refreshed successfully, expires at {self.token_expiry}")
                
                # Save the new tokens to file
                self.save_tokens()
                
                return token_data
            else:
                error_msg = f"Token refresh failed: {response.status_code} - {response.text}"
                print(f"[QB ERROR] {error_msg}")
                raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Token refresh network error: {str(e)}"
            print(f"[QB ERROR] {error_msg}")
            raise Exception(error_msg)
    
    def ensure_valid_token(self):
        """Ensure access token is valid, refresh if needed"""
        if not self.access_token:
            raise Exception("No access token available. Please authenticate first.")
        
        if self.token_expiry and datetime.now() >= self.token_expiry - timedelta(minutes=5):
            print("[QB] Token expiring soon, refreshing...")
            self.refresh_access_token()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated request to QuickBooks API"""
        self.ensure_valid_token()
        
        if not self.realm_id:
            raise Exception("No realm_id (Company ID) set. Please set it after authentication.")
        
        url = f"{self.base_url}/v3/company/{self.realm_id}/{endpoint}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"QuickBooks API error: {response.status_code} - {response.text}")
    
    # ========== PRODUCTS/ITEMS ==========
    
    def get_items(self, max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch items (products/services) from QuickBooks"""
        query = f"SELECT * FROM Item MAXRESULTS {max_results} STARTPOSITION {start_position}"
        params = {'query': query}
        
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('Item', [])
    
    def get_item_by_id(self, item_id: str) -> Dict:
        """Fetch specific item by ID - returns all fields including Description"""
        result = self._make_request('GET', f'item/{item_id}')
        return result.get('Item', {})
    
    def get_all_items(self) -> List[Dict]:
        """Fetch all items with pagination"""
        all_items = []
        start_position = 1
        max_results = 100
        
        while True:
            items = self.get_items(max_results=max_results, start_position=start_position)
            if not items:
                break
            
            all_items.extend(items)
            
            if len(items) < max_results:
                break
            
            start_position += max_results
        
        return all_items
    
    # ========== INVOICES ==========
    
    def get_invoices(self, start_date: str = None, end_date: str = None, 
                     max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch invoices from QuickBooks
        
        Args:
            start_date: Format YYYY-MM-DD
            end_date: Format YYYY-MM-DD
        """
        query = f"SELECT * FROM Invoice"
        
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        
        query += f" MAXRESULTS {max_results} STARTPOSITION {start_position}"
        
        params = {'query': query}
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('Invoice', [])
    
    def get_invoice_by_id(self, invoice_id: str) -> Dict:
        """Fetch specific invoice by ID"""
        result = self._make_request('GET', f'invoice/{invoice_id}')
        return result.get('Invoice', {})
    
    # ========== CREDIT MEMOS ==========
    
    def get_credit_memos(self, start_date: str = None, end_date: str = None,
                         max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch credit memos from QuickBooks"""
        query = f"SELECT * FROM CreditMemo"
        
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        
        query += f" MAXRESULTS {max_results} STARTPOSITION {start_position}"
        
        params = {'query': query}
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('CreditMemo', [])
    
    # ========== CUSTOMERS ==========
    
    def get_customers(self, max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch customers from QuickBooks"""
        query = f"SELECT * FROM Customer MAXRESULTS {max_results} STARTPOSITION {start_position}"
        params = {'query': query}
        
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('Customer', [])
    
    def get_customer_by_id(self, customer_id: str) -> Dict:
        """Fetch specific customer by ID"""
        result = self._make_request('GET', f'customer/{customer_id}')
        return result.get('Customer', {})
    
    # ========== VENDORS ==========
    
    def get_vendors(self, max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch vendors from QuickBooks"""
        query = f"SELECT * FROM Vendor MAXRESULTS {max_results} STARTPOSITION {start_position}"
        params = {'query': query}
        
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('Vendor', [])
    
    def get_vendor_by_id(self, vendor_id: str) -> Dict:
        """Fetch specific vendor by ID"""
        result = self._make_request('GET', f'vendor/{vendor_id}')
        return result.get('Vendor', {})
    
    # ========== PURCHASE ORDERS (for stock tracking) ==========
    
    def get_purchase_orders(self, start_date: str = None, end_date: str = None,
                           max_results: int = 100, start_position: int = 1) -> List[Dict]:
        """Fetch purchase orders from QuickBooks"""
        query = f"SELECT * FROM PurchaseOrder"
        
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        
        query += f" MAXRESULTS {max_results} STARTPOSITION {start_position}"
        
        params = {'query': query}
        result = self._make_request('GET', 'query', params=params)
        return result.get('QueryResponse', {}).get('PurchaseOrder', [])
    
    # ========== COMPANY INFO ==========
    
    def get_company_info(self) -> Dict:
        """Fetch company information from QuickBooks"""
        result = self._make_request('GET', f'companyinfo/{self.realm_id}')
        return result.get('CompanyInfo', {})
    
    def detect_region(self) -> str:
        """Detect QuickBooks region/country from company info"""
        try:
            company_info = self.get_company_info()
            
            # Try to get country from company address
            country = company_info.get('Country', '')
            if country:
                # Map common country values to regions
                country_mapping = {
                    'US': 'US', 'USA': 'US', 'United States': 'US',
                    'GB': 'UK', 'UK': 'UK', 'United Kingdom': 'UK', 'England': 'UK', 'Scotland': 'UK', 'Wales': 'UK',
                    'CA': 'CA', 'Canada': 'CA',
                    'AU': 'AU', 'Australia': 'AU',
                    'IN': 'IN', 'India': 'IN',
                    'FR': 'FR', 'France': 'FR'
                }
                
                region = country_mapping.get(country.upper().strip(), 'US')  # Default to US
                print(f"[QB] Detected region: {region} (from country: {country})")
                return region
            
            # Fallback: check base URL
            if 'sandbox-quickbooks.api.intuit.com' in self.base_url or 'quickbooks.api.intuit.com' in self.base_url:
                return 'US'  # Standard US endpoints
            
            # Default to US if unable to determine
            print("[QB] Unable to determine region, defaulting to US")
            return 'US'
            
        except Exception as e:
            print(f"[QB] Error detecting region: {e}")
            return 'US'  # Default fallback
    
    # ========== PERSISTENCE ==========
    
    def save_tokens(self, filepath: str = 'quickbooks_tokens.json'):
        """Save tokens to file for persistence"""
        token_data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'realm_id': self.realm_id,
            'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None
        }
        
        with open(filepath, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"[QB] Tokens saved to {filepath}")
    
    def load_tokens(self, filepath: str = 'quickbooks_tokens.json') -> bool:
        """Load tokens from file"""
        try:
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            self.realm_id = token_data.get('realm_id')
            
            expiry_str = token_data.get('token_expiry')
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
            
            print(f"[QB] Tokens loaded from {filepath}")
            return True
        except FileNotFoundError:
            print(f"[QB] No token file found at {filepath}")
            return False
        except Exception as e:
            print(f"[QB] Error loading tokens: {e}")
            return False

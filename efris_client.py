import os
import json
import uuid
import base64
import gzip
import requests
from datetime import datetime, timedelta
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend
import urllib3

# Disable SSL warnings for test environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# CRITICAL: Global timeout for all EFRIS requests (prevents hung workers)
EFRIS_REQUEST_TIMEOUT = int(os.getenv("EFRIS_TIMEOUT", "30"))  # 30 seconds default

class EfrisManager:
    def __init__(self, tin, device_no=None, base_url=None, client_id=None, client_secret=None, cert_path=None, key_path=None, test_mode=False):
        self.tin = tin
        self.device_no = device_no or f"{tin}_02"  # Default to TIN_02 if not specified
        self.aes_key = None  # Will be populated after T104 key exchange
        self.server_sign = None  # Server signature from T104
        self.aes_key_expires_at = None  # Track when the AES key expires
        self.key_expiry_hours = 24  # AES key valid for 24 hours (configurable)
        self.request_timeout = EFRIS_REQUEST_TIMEOUT  # Use global timeout
        
        if test_mode:
            base_url = base_url or 'https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation'
            self.base_url = base_url
            self.test_mode = True
            self.verify_ssl = False  # Disable SSL verification for test server
            self.session = requests.Session()
            self.session.verify = False  # Disable SSL verification for test environment
            self._load_certificate(cert_path or os.getenv('EFRIS_CERT_PATH'))
            self.registration_details = {}  # Initialize
            print(f"[EFRIS] Initialized with TIN: {self.tin}, Device: {self.device_no}, Test Mode: YES, URL: {base_url}, SSL Verify: NO, Timeout: {self.request_timeout}s")
            # self._perform_handshake()  # Commented out for now
        else:
            # Production EFRIS endpoint
            base_url = base_url or 'https://efris.ura.go.ug/efrisws/ws/taapp/getInformation'
            self.base_url = base_url
            self.test_mode = False
            self.verify_ssl = True  # Enable SSL verification for production
            self.session = requests.Session()
            self.session.verify = True  # Enable SSL verification for production environment
            self._load_certificate(cert_path or os.getenv('EFRIS_CERT_PATH'))
            self.registration_details = {}  # Initialize
            print(f"[EFRIS] Initialized with TIN: {self.tin}, Device: {self.device_no}, Production Mode: YES, URL: {base_url}, SSL Verify: YES, Timeout: {self.request_timeout}s")
        self.base_url = base_url

    def _load_certificate(self, cert_path):
        print(f"Loading certificate from {cert_path}")
        if cert_path and os.path.exists(cert_path):
            try:
                with open(cert_path, 'rb') as f:
                    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(f.read(), b'123456')
                self.private_key = private_key
                self.certificate = certificate
                print("Certificate loaded successfully")
            except Exception as e:
                print(f"Certificate load error: {e}")
                raise
        else:
            print("No certificate path or file not found")
            self.private_key = None
            self.certificate = None

    def _sign(self, data_str):
        """RSA sign data using private key (SHA1 with PKCS1v15 padding)
        
        EFRIS Signature Process:
        1. Take the content string (may be JSON or empty)
        2. Hash with SHA1 (NOT SHA256!)
        3. Sign with private key using PKCS1v15 padding
        4. Base64 encode the signature
        
        The signature is calculated over the 'content' field value only,
        NOT the entire payload.
        """
        if not self.private_key:
            raise Exception("Private key not loaded. Certificate must be provided.")
        
        # Convert to bytes if string
        if isinstance(data_str, str):
            data_bytes = data_str.encode('utf-8')
        else:
            data_bytes = data_str
        
        # RSA sign with SHA1 and PKCS1v15 padding (EFRIS uses SHA1, not SHA256)
        signature = self.private_key.sign(
            data_bytes,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        
        # Return Base64 encoded signature
        sig_b64 = base64.b64encode(signature).decode('utf-8')
        
        # Debug: Log what we're signing
        debug_content = data_str if isinstance(data_str, str) else str(data_str)
        print(f"[SIGN] Content length: {len(debug_content)}")
        print(f"[SIGN] Content: {debug_content[:100] if debug_content else '(empty)'}")
        print(f"[SIGN] Signature length: {len(sig_b64)}")
        
        return sig_b64

    def _build_handshake_payload(self, interface_code, content):
        """Build handshake payload
        
        For T101 (time sync) and T104 (key exchange): These are initialization requests
        that typically don't require signatures since we don't have the AES key yet.
        
        For T103 (get parameters): This request comes AFTER key exchange and may require
        signature with the content (TIN).
        """
        from datetime import datetime
        global_info = {
            "appId": "AP04",
            "version": "1.1.20191201",
            "dataExchangeId": uuid.uuid4().hex,
            "interfaceCode": interface_code,
            "requestCode": "TP",
            "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "responseCode": "TA",
            "userName": "admin",
            "deviceMAC": "FFFFFFFFFFFF",
            "deviceNo": self.device_no,
            "tin": self.tin,
            "brn": "",
            "taxpayerID": "1",
            "longitude": "116.397128",
            "latitude": "39.916527",
            "agentType": "0",
            "extendField": {
                "responseDateFormat": "dd/MM/yyyy",
                "responseTimeFormat": "dd/MM/yyyy HH:mm:ss",
                "referenceNo": "21PL010020807",
                "operatorName": "administrator",
                "itemDescription": "28300 test services both",
                "currency": "UGX",
                "grossAmount": "25",
                "taxAmount": "3.7985",
                "offlineInvoiceException": {
                    "errorCode": "",
                    "errorMsg": ""
                }
            }
        }
        data_desc = {
            "codeType": "0",
            "encryptCode": "1" if interface_code == "T103" else "0",  # T103 needs encryptCode 1
            "zipCode": "0"
        }
        
        # For handshake requests, signature depends on interface
        # T101: No signature (time sync - public request)
        # T104: No signature (key exchange - public request)  
        # T103: No signature (get parameters - empty content request)
        if interface_code == "T101":
            sig = ""  # T101 time sync doesn't require signature
            print(f"[T101] Time sync - no signature")
        elif interface_code == "T104":
            sig = ""  # T104 key exchange doesn't require signature
            print(f"[T104] Key exchange - no signature")
        elif interface_code == "T103":
            # T103 with empty content - no signature
            sig = ""
            print(f"[T103] Get parameters - no signature (encryptCode=1)")
        else:
            sig = self._sign(content) if content else ""
            print(f"[{interface_code}] Signature: {sig[:30] if sig else '(empty)'}")
        
        payload = {
            "data": {
                "content": content,
                "signature": sig,
                "dataDescription": data_desc
            },
            "globalInfo": global_info,
            "returnStateInfo": {
                "returnCode": "",
                "returnMessage": ""
            }
        }
        return payload

    def _build_request_payload(self, interface_code, content, encrypt_code=1):
        """Build request payload with proper encryption and signing
        
        For encrypt_code = 0: No encryption
        For encrypt_code = 1: RSA sign only (content as-is)
        For encrypt_code = 2: AES encrypt content + RSA sign the encrypted content
        
        Documentation flow:
        5. Encrypt the request content json of the given interface using the AES key
        6. Base64 encode the result and add it to the content field
        7. Use private key to RSA sign the content (encrypted or plain)
        8. Add the resulting string to the signature field
        """
        # Ensure we have a valid AES key before building request
        self.ensure_authenticated()
        
        from datetime import datetime
        global_info = {
            "appId": "AP04",
            "version": "1.1.20191201",
            "dataExchangeId": uuid.uuid4().hex,
            "interfaceCode": interface_code,
            "requestCode": "TP",
            "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "responseCode": "TA",
            "userName": "admin",
            "deviceMAC": "FFFFFFFFFFFF",
            "deviceNo": self.device_no,
            "tin": self.tin,
            "brn": "",
            "taxpayerID": "1",
            "longitude": "116.397128",
            "latitude": "39.916527",
            "agentType": "0",
            "extendField": {
                "responseDateFormat": "dd/MM/yyyy",
                "responseTimeFormat": "dd/MM/yyyy HH:mm:ss",
                "referenceNo": "21PL010020807",
                "operatorName": "administrator",
                "itemDescription": "28300 test services both",
                "currency": "UGX",
                "grossAmount": "25",
                "taxAmount": "3.7985",
                "offlineInvoiceException": {
                    "errorCode": "",
                    "errorMsg": ""
                }
            }
        }
        data_desc = {
            "codeType": "0",
            "encryptCode": str(encrypt_code),
            "zipCode": "0"
        }
        
        # Prepare content and signature based on encrypt code
        if encrypt_code == 2:
            # AES encrypt the content, then sign the encrypted content
            encrypted_content = self._encrypt_aes(content)
            content_to_use = encrypted_content
            sig = self._sign(encrypted_content)
        elif encrypt_code == 1:
            # Base64 encode plain content, then sign the base64 encoded content
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            content_to_use = content_b64
            sig = self._sign(content_b64)  # Sign the base64 encoded content
        else:
            # encrypt_code == 0: No encoding, no signature
            content_to_use = content
            sig = ""
        
        payload = {
            "data": {
                "content": content_to_use,
                "signature": sig,
                "dataDescription": data_desc
            },
            "globalInfo": global_info,
            "returnStateInfo": {
                "returnCode": "",
                "returnMessage": ""
            }
        }
        return payload

    def _encrypt_aes(self, plain_text):
        """Encrypt content using AES key obtained from T104
        
        EFRIS uses AES-128-ECB mode (no IV needed).
        Steps:
        1. Ensure valid AES key is available (cached or fresh)
        2. Encrypt plain_text using AES-ECB with the symmetric key
        3. Base64 encode the encrypted result
        4. Return the encoded result for use in content field
        """
        # Ensure we have a valid AES key before encrypting
        self.ensure_authenticated()
        
        if not self.aes_key:
            raise Exception("AES key not available after authentication")
        
        if len(self.aes_key) != 16:
            raise Exception(f"Invalid AES key size: {len(self.aes_key)} bytes (expected 16)")
        
        key = self.aes_key
        
        # Use ECB mode (no IV needed) - matches friend's Rust implementation
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text.encode('utf-8')) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return encrypted data, Base64 encoded (no IV prepended for ECB)
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt_aes(self, encrypted_text):
        """Decrypt AES-ECB encrypted content
        
        EFRIS uses ECB mode for response decryption (no IV needed).
        Format: Base64(encrypted_data)
        """
        key = self.aes_key
        
        # Remove any whitespace from base64 string
        encrypted_text_clean = encrypted_text.strip()
        
        # Decode base64
        encrypted = base64.b64decode(encrypted_text_clean)
        
        # Check if length is multiple of block size (16 bytes for AES)
        if len(encrypted) % 16 != 0:
            print(f"[DECRYPT] Warning: Encrypted data length {len(encrypted)} is not a multiple of 16")
            print(f"[DECRYPT] Base64 string length: {len(encrypted_text_clean)}")
            # Try to pad to block size
            padding_needed = 16 - (len(encrypted) % 16)
            print(f"[DECRYPT] Adding {padding_needed} bytes of padding")
            encrypted = encrypted + (b'\x00' * padding_needed)
        
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain_data = unpadder.update(padded_data) + unpadder.finalize()
        return plain_data.decode()
    
    def _decrypt_aes_ecb(self, encrypted_text_b64):
        """Decrypt AES-ECB encrypted content
        
        EFRIS server uses ECB mode for T103 response encryption.
        Format: Base64(encrypted_data) - no IV prepended
        """
        key = self.aes_key
        encrypted = base64.b64decode(encrypted_text_b64)
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain_data = unpadder.update(padded_data) + unpadder.finalize()
        return plain_data.decode()

    def get_registration_details(self):
        """Get registration details using T103"""
        # self.ensure_authenticated()
        content = json.dumps({"tin": self.tin}, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T103", content, encrypt_code=1)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        print(f"[T103] Response status: {response.status_code}")
        print(f"[T103] Response headers: {response.headers}")
        print(f"[T103] Response text: {response.text[:500]}")  # First 500 chars
        
        if response.status_code == 200:
            try:
                if not response.text or response.text.strip() == "":
                    return {"error": "Empty response from EFRIS server"}
                return response.json()
            except json.JSONDecodeError as e:
                return {
                    "error": "Invalid JSON response from EFRIS",
                    "details": str(e),
                    "response_text": response.text[:200]
                }
        else:
            return {"error": f'API Error {response.status_code}', "details": response.text}

    def get_goods_and_services(self, page_no=1, page_size=10, goods_code=None, goods_name=None):
        """Get goods and services using T127 - Goods/Services Inquiry
        
        T127 is used to query the taxpayer's goods and services catalog from EFRIS.
        Returns paginated list of registered products/services.
        
        Args:
            page_no: Page number (default: 1)
            page_size: Number of records per page (default: 10)
            goods_code: Optional filter by goods code
            goods_name: Optional filter by goods name
            
        Returns:
            Response containing list of goods/services with details
        """
        # Ensure we have a valid AES key for decryption
        self.ensure_authenticated()
        
        # Build request content according to T127 specification
        request_content = {
            "pageNo": str(page_no),
            "pageSize": str(page_size)
        }
        
        # Add optional filters if provided
        if goods_code:
            request_content["goodsCode"] = goods_code
        if goods_name:
            request_content["goodsName"] = goods_name
            
        content = json.dumps(request_content, separators=(',', ':'), sort_keys=True)
        # T127 requires AES encryption (encryptCode=2)
        payload = self._build_request_payload("T127", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"[T127] Full response: {json.dumps(result, indent=2)}")
            print(f"[T127] Response status: {result.get('status')}")
            print(f"[T127] Response message: {result.get('msg')}")
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    print(f"[T127] Response is encrypted (encryptCode=2)")
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        print(f"[T127] Encrypted content length: {len(encrypted_content)}")
                        print(f"[T127] Encrypted content (first 100 chars): {encrypted_content[:100]}")
                        
                        # Check if it's gzip compressed (starts with H4sI which is base64 of gzip magic)
                        if encrypted_content.startswith('H4sI'):
                            print(f"[T127] Content appears to be gzip compressed")
                            # Decompress first
                            compressed_data = base64.b64decode(encrypted_content)
                            decompressed_data = gzip.decompress(compressed_data)
                            print(f"[T127] Gzip decompression successful! Decompressed size: {len(decompressed_data)}")
                            
                            # The decompressed data might still be AES encrypted
                            # Try to decrypt it
                            try:
                                # Re-encode to base64 for AES decryption
                                decompressed_b64 = base64.b64encode(decompressed_data).decode('utf-8')
                                decrypted_content = self._decrypt_aes(decompressed_b64)
                                print(f"[T127] AES decryption successful!")
                            except:
                                # If AES fails, it might be plain text
                                decrypted_content = decompressed_data.decode('utf-8')
                                print(f"[T127] Content was not encrypted, just compressed")
                        else:
                            # Try AES decryption only
                            decrypted_content = self._decrypt_aes(encrypted_content)
                            print(f"[T127] AES decryption successful!")
                        
                        print(f"[T127] Decrypted content length: {len(decrypted_content)}")
                        print(f"[T127] Decrypted content: {decrypted_content[:200] if decrypted_content else 'EMPTY'}")
                        parsed_content = json.loads(decrypted_content)
                        print(f"[T127] Parsed content keys: {parsed_content.keys() if isinstance(parsed_content, dict) else 'not a dict'}")
                        result['data']['decrypted_content'] = parsed_content
                        print(f"[T127] Decryption successful!")
                    else:
                        print(f"[T127] No encrypted content found")
                else:
                    print(f"[T127] Response is not encrypted or encryptCode != 2")
                    print(f"[T127] encryptCode: {result.get('data', {}).get('dataDescription', {}).get('encryptCode')}")
            except Exception as e:
                print(f"[T127] Warning: Failed to decrypt response content: {e}")
                import traceback
                traceback.print_exc()
                # Return result anyway with raw content
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def get_code_list(self, code_type):
        """Query system dictionary using T115 - System Dictionary Update
        
        This returns system parameters including:
        - currencyType: List of currencies (101=UGX, 102=USD, etc.)
        - rateUnit: List of units of measure (101=per stick, 102=per litre, etc.)
        - exciseStandardRateType: Excise duty types
        - And other system parameters
        
        Args:
            code_type: Not used for T115, kept for API compatibility
        
        Returns:
            Dictionary of system parameters with units of measure in rateUnit field
        """
        self.ensure_authenticated()
        
        # T115 doesn't require any content, just send empty dict
        content_dict = {}
        plain_content = json.dumps(content_dict, separators=(',', ':'), sort_keys=True)
        
        # Build payload with no encryption (encrypt_code=0 based on PDF)
        payload = self._build_request_payload("T115", plain_content, encrypt_code=2)
        
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code == 200:
            result = response.json()
            print(f"[T115] Response returnCode: {result.get('returnStateInfo', {}).get('returnCode')}")
            
            # Try to decompress/decrypt the response
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        # Check if it's gzip compressed (starts with H4sI which is base64 of gzip magic)
                        if encrypted_content.startswith('H4sI'):
                            print(f"[T115] Content appears to be gzip compressed")
                            # Decompress first
                            compressed_data = base64.b64decode(encrypted_content)
                            decompressed_data = gzip.decompress(compressed_data)
                            print(f"[T115] Gzip decompression successful! Decompressed size: {len(decompressed_data)}")
                            
                            # The decompressed data might still be AES encrypted
                            # Try to decrypt it
                            try:
                                # Re-encode to base64 for AES decryption
                                decompressed_b64 = base64.b64encode(decompressed_data).decode('utf-8')
                                decrypted_content = self._decrypt_aes(decompressed_b64)
                                print(f"[T115] AES decryption successful!")
                            except:
                                # If AES fails, it might be plain text
                                decrypted_content = decompressed_data.decode('utf-8')
                                print(f"[T115] Content was not encrypted, just compressed")
                        else:
                            # Try AES decryption only
                            decrypted_content = self._decrypt_aes(encrypted_content)
                            print(f"[T115] AES decryption successful!")
                        
                        parsed_content = json.loads(decrypted_content)
                        result['data']['decrypted_content'] = parsed_content
            except Exception as e:
                print(f"[T115] Warning: Failed to decompress/decrypt response content: {e}")
                import traceback
                traceback.print_exc()
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def upload_goods(self, products):
        """Upload/Register goods and services using T130
        
        Register or update product information in EFRIS system.
        
        Args:
            products: List of product dictionaries with the following structure:
                [
                    {
                        "operationType": "101",  # 101=Add, 102=Update
                        "goodsName": "Product Name",
                        "goodsCode": "PRODUCT001",
                        "measureUnit": "101",  # Unit code (e.g., 101=Piece)
                        "unitPrice": "10000",
                        "currency": "101",  # 101=UGX
                        "commodityCategoryId": "1234567890",  # Category ID from EFRIS
                        "haveExciseTax": "102",  # 101=Yes, 102=No
                        "description": "Product description",
                        "stockPrewarning": "10",  # Low stock warning threshold
                        "pieceMeasureUnit": "101",
                        "havePieceUnit": "102",  # 101=Yes, 102=No
                        "pieceUnitPrice": "10000",
                        "packageScaledValue": "1",
                        "pieceScaledValue": "1",
                        "exciseDutyCode": "",  # Required if haveExciseTax=101
                    }
                ]
        
        Returns:
            Response containing list of products with success/failure status for each
        """
        # T130 requires AES encryption (encryptCode=2)
        content = json.dumps(products, separators=(',', ':'), sort_keys=True)
        print(f"[T130] Uploading {len(products)} products")
        print(f"[T130] Product data: {content[:500]}...")  # First 500 chars
        payload = self._build_request_payload("T130", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[T130] Response status: {result.get('status')}")
            print(f"[T130] Response message: {result.get('msg')}")
            print(f"[T130] Return state: {result.get('returnStateInfo', {})}")
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    print(f"[T130] Response is encrypted")
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        print(f"[T130] Encrypted content length: {len(encrypted_content)}")
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        print(f"[T130] Decrypted successfully")
                        parsed = json.loads(decrypted_content)
                        result['data']['decrypted_content'] = parsed
                        print(f"[T130] Decrypted response: {parsed}")
                else:
                    print(f"[T130] Response not encrypted")
                    if result.get('data', {}).get('content'):
                        print(f"[T130] Content: {result['data']['content']}")
            except Exception as e:
                print(f"[T130] Warning: Failed to decrypt response content: {e}")
                import traceback
                traceback.print_exc()
                # Return result anyway with raw content
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def stock_increase(self, stock_data):
        """Increase stock for already registered products using T131
        
        Args:
            stock_data: Dictionary with the following structure:
                {
                    "goodsStockIn": {
                        "operationType": "101",  # Always 101 for stock increase
                        "supplierTin": "1234567890",
                        "supplierName": "Supplier Name",
                        "remarks": "Stock purchase",
                        "stockInDate": "2026-01-01",  # YYYY-MM-DD format
                        "stockInType": "102",  # 102=Purchase, 103=Production, etc.
                        "productionBatchNo": "",
                        "productionDate": ""
                    },
                    "goodsStockInItem": [
                        {
                            "goodsCode": "PRODUCT001",
                            "quantity": 100,
                            "unitPrice": 5000
                        }
                    ]
                }
        
        Returns:
            Response containing stock update status for each item
        """
        print(f"[T131] Stock increase request: {json.dumps(stock_data, indent=2)[:500]}")
        
        content = json.dumps(stock_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T131", content, encrypt_code=2)
        
        print(f"[T131] Sending request to EFRIS...")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        print(f"[T131] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"[T131] Response returnCode: {result.get('returnStateInfo', {}).get('returnCode')}")
            print(f"[T131] Response returnMessage: {result.get('returnStateInfo', {}).get('returnMessage')}")
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
                        print(f"[T131] Decrypted response: {json.dumps(result['data']['decrypted_content'], indent=2)[:500]}")
            except Exception as e:
                print(f"[T131] Warning: Failed to decrypt response content: {e}")
                
            return result
        else:
            error_msg = f'API Error {response.status_code}: {response.text}'
            print(f"[T131] {error_msg}")
            return error_msg

    def upload_invoice(self, invoice_data):
        """Upload and fiscalize invoice using T109
        
        Args:
            invoice_data: Dictionary with the following structure:
                {
                    "sellerDetails": {
                        "tin": "1014409555",
                        "ninBrn": "",
                        "legalName": "Company Legal Name",
                        "businessName": "Company Business Name",
                        "address": "Company Address",
                        "mobilePhone": "0700000000",
                        "linePhone": "",
                        "emailAddress": "email@example.com",
                        "placeOfBusiness": "Kampala",
                        "referenceNo": "INV001"
                    },
                    "basicInformation": {
                        "operator": "admin",
                        "invoiceNo": "",  # Leave empty for auto-generation
                        "antifakeCode": "",  # Anti-fake code (optional)
                        "deviceNo": "",  # Device number (optional) 
                        "issuedDate": "2024-01-01 10:00:00",  # Invoice date and time
                        "operator": "admin",
                        "currency": "UGX",
                        "oriInvoiceId": "",  # Original invoice ID (for modifications)
                        "invoiceType": "1",  # 1=Normal invoice, 2=E-invoice
                        "invoiceKind": "1",  # 1=Sale, 2=Purchase
                        "dataSource": "106",  # 106=System interface
                        "invoiceIndustryCode": "101",  # Industry code
                        "isBatch": "0"  # 0=Single invoice, 1=Batch
                    },
                    "buyerDetails": {
                        "buyerTin": "",
                        "buyerNinBrn": "",
                        "buyerPassportNum": "",
                        "buyerLegalName": "Customer Name",
                        "buyerBusinessName": "",
                        "buyerAddress": "Customer Address",
                        "buyerMobilePhone": "0700000000",
                        "buyerLinePhone": "",
                        "buyerPlaceOfBusi": "",
                        "buyerEmail": "",
                        "buyerCitizenship": "",
                        "buyerSector": "",
                        "buyerReferenceNo": "",
                        "buyerType": "1"  # 0=Business (TIN required), 1=Individual (no TIN), 2=Foreign, 3=Exempt
                    },
                    "goodsDetails": [
                        {
                            "item": "Product Name",
                            "itemCode": "PRODUCT001",
                            "qty": "10",
                            "unitOfMeasure": "101",
                            "unitPrice": "5000",
                            "total": "50000",
                            "taxRate": "0.18",
                            "tax": "9000",
                            "discountTotal": "",  # Empty when discountFlag is 2
                            "discountTaxRate": "",  # Empty when no discount
                            "orderNumber": "0",
                            "discountFlag": "2",  # 2=No discount, 1=Has discount
                            "deemedFlag": "2",  # 2=Not deemed, 1=Deemed
                            "exciseFlag": "2",  # 2=No excise, 1=Has excise
                            "categoryId": "",
                            "categoryName": "",
                            "goodsCategoryId": "50202306",
                            "goodsCategoryName": "Soft drinks",
                            "exciseUnit": "",
                            "exciseCurrency": "",
                            "exciseTax": "0",
                            "pack": "1",
                            "stick": "1",
                            "exciseRateName": ""
                        }
                    ],
                    "taxDetails": [
                        {
                            "taxCategoryCode": "01",  # Standard VAT
                            "netAmount": "50000",
                            "taxRate": "0.18",
                            "taxAmount": "9000",
                            "grossAmount": "59000",
                            "tax": "9000",
                            "currencyType": "UGX"
                        }
                    ],
                    "summary": {
                        "netAmount": "50000",
                        "taxAmount": "9000",
                        "grossAmount": "59000",
                        "itemCount": "1",
                        "modeCode": "0",
                        "remarks": "",
                        "qrCode": ""
                    },
                    "payWay": [
                        {
                            "paymentMode": "101",  # 101=Cash
                            "paymentAmount": 59000,
                            "orderNumber": "a"
                        }
                    ],
                    "extend": {
                        "reason": "",
                        "reasonCode": ""
                    }
                }
        
        Returns:
            Response containing fiscalized invoice details including FDN
        """
        content = json.dumps(invoice_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T109", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                data = result.get('data', {})
                encrypted_content = data.get('content', '')
                
                if encrypted_content and isinstance(encrypted_content, str):
                    # Try to decrypt
                    decrypted_content = self._decrypt_aes(encrypted_content)
                    
                    # Parse decrypted content
                    if decrypted_content:
                        try:
                            # Try parsing as JSON
                            parsed_content = json.loads(decrypted_content)
                            result['data']['decrypted_content'] = parsed_content
                            print(f"[T109] Invoice uploaded successfully")
                            print(f"[T109] Decrypted response keys: {parsed_content.keys() if isinstance(parsed_content, dict) else type(parsed_content)}")
                            print(f"[T109] Decrypted response: {json.dumps(parsed_content, indent=2)[:1000]}")
                            if isinstance(parsed_content, dict):
                                # Try multiple possible key names for FDN
                                fdn = (parsed_content.get('fdn') or 
                                       parsed_content.get('invoiceNo') or 
                                       parsed_content.get('FDN') or
                                       parsed_content.get('basicInformation', {}).get('invoiceNo'))
                                invoice_id = (parsed_content.get('invoiceId') or 
                                              parsed_content.get('id') or
                                              parsed_content.get('basicInformation', {}).get('invoiceId'))
                                if fdn:
                                    print(f"[T109] FDN: {fdn}")
                                if invoice_id:
                                    print(f"[T109] Invoice ID: {invoice_id}")
                        except json.JSONDecodeError:
                            # If not JSON, store as string
                            result['data']['decrypted_content'] = decrypted_content
                            print(f"[T109] Response decrypted (non-JSON): {decrypted_content[:100]}")
                else:
                    # Content might already be decrypted or in different format
                    print(f"[T109] Response received (no encryption)")
                    if isinstance(data.get('content'), dict):
                        result['data']['decrypted_content'] = data['content']
                        
            except Exception as e:
                print(f"[T109] Response handling: {e}")
                print(f"[T109] Raw response data: {result.get('data', {})}")
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def upload_credit_note(self, credit_note_data):
        """Upload credit note to EFRIS using T111
        
        Args:
            credit_note_data: Dictionary with the following structure:
                {
                    "oriInvoiceId": "original_invoice_id",
                    "oriInvoiceNo": "original_invoice_number",
                    "reasonCode": "102",  # Reason code for credit note
                    "reason": "Product return",
                    "applicationTime": "2026-01-01 10:00:00",
                    "invoiceApplyCategoryCode": "101",
                    "currency": "UGX",
                    "contactName": "Contact Person",
                    "contactMobileNum": "0700000000",
                    "contactEmail": "contact@example.com",
                    "source": "106",
                    "remarks": "Credit note remarks",
                    "sellersReferenceNo": "CN001",
                    "goodsDetails": [
                        {
                            "item": "Product Name",
                            "itemCode": "PRODUCT001",
                            "qty": "5",
                            "unitOfMeasure": "101",
                            "unitPrice": "5000",
                            "total": "25000",
                            "taxRate": "0.18",
                            "tax": "4500",
                            "discountTotal": "0",
                            "orderNumber": "0",
                            "deemedFlag": "0",
                            "exciseFlag": "0",
                            "categoryId": "",
                            "categoryName": "",
                            "goodsCategoryId": "50202306",
                            "goodsCategoryName": "Soft drinks",
                            "exciseCurrency": "",
                            "exciseTax": "0",
                            "pack": "1",
                            "stick": "1"
                        }
                    ]
                }
        
        Returns:
            Response containing credit note details
        """
        content = json.dumps(credit_note_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T111", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
            except Exception as e:
                print(f"[T111] Warning: Failed to decrypt response content: {e}")
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_invoice(self, query_params):
        """Query invoices/receipts using T106
        
        Args:
            query_params: Dictionary with the following structure:
                {
                    "buyerLegalName": "Customer Name",  # Optional filter
                    "startDate": "2026-01-01",  # YYYY-MM-DD format
                    "endDate": "2026-01-31",    # YYYY-MM-DD format
                    "invoiceKind": "1",  # 1=Invoice, 2=Receipt
                    "pageNo": "1",
                    "pageSize": "10"
                }
        
        Returns:
            Response containing list of invoices/receipts matching criteria
        """
        # Ensure we have a valid AES key for decryption
        self.ensure_authenticated()
        
        content = json.dumps(query_params, separators=(',', ':'), sort_keys=True)
        print(f"[T106] Query params: {query_params}")
        print(f"[T106] Content to send: {content}")
        payload = self._build_request_payload("T106", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[T106] Response status code: {result.get('returnStateInfo', {}).get('returnCode')}")
            print(f"[T106] Response message: {result.get('returnStateInfo', {}).get('returnMessage')}")
            
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    print(f"[T106] Encrypted content length: {len(encrypted_content) if encrypted_content else 0}")
                    if encrypted_content:
                        # Check if it's gzip compressed (starts with H4sI which is base64 of gzip magic)
                        if encrypted_content.startswith('H4sI'):
                            print(f"[T106] Content appears to be gzip compressed")
                            # Decompress first
                            compressed_data = base64.b64decode(encrypted_content)
                            decompressed_data = gzip.decompress(compressed_data)
                            print(f"[T106] Gzip decompression successful! Decompressed size: {len(decompressed_data)}")
                            
                            # The decompressed data might still be AES encrypted
                            # Try to decrypt it
                            try:
                                # Re-encode to base64 for AES decryption
                                decompressed_b64 = base64.b64encode(decompressed_data).decode('utf-8')
                                decrypted_content = self._decrypt_aes(decompressed_b64)
                                print(f"[T106] AES decryption successful!")
                            except:
                                # If AES fails, it might be plain text
                                decrypted_content = decompressed_data.decode('utf-8')
                                print(f"[T106] Content was not encrypted, just compressed")
                        else:
                            # Try AES decryption only
                            decrypted_content = self._decrypt_aes(encrypted_content)
                            print(f"[T106] AES decryption successful!")
                        
                        print(f"[T106] Decrypted content length: {len(decrypted_content)}")
                        print(f"[T106] Decrypted content (first 200 chars): {decrypted_content[:200]}")
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
                        print(f"[T106] Decryption successful! Keys: {result['data']['decrypted_content'].keys()}")
                    else:
                        print(f"[T106] No encrypted content to decrypt")
            except Exception as e:
                print(f"[T106] Warning: Failed to decrypt response content: {e}")
                import traceback
                traceback.print_exc()
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_invoices(self, query_params):
        """Alias for query_invoice - Query invoices/receipts using T106
        
        This method exists for API consistency (plural naming).
        """
        return self.query_invoice(query_params)

    def get_invoice_details(self, invoice_no):
        """Get invoice details by invoice number using T108
        
        Args:
            invoice_no: Invoice number (e.g., "1234567890123456789")
        
        Returns:
            Response containing complete invoice details
        """
        content = json.dumps({"invoiceNo": invoice_no}, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T108", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
            except Exception as e:
                print(f"[T108] Warning: Failed to decrypt response content: {e}")
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_credit_notes(self, query_params):
        """Query credit notes using T112
        
        Args:
            query_params: Dictionary with the following structure:
                {
                    "referenceNo": "",  # Optional seller's reference number
                    "oriInvoiceNo": "",  # Optional original invoice number
                    "invoiceNo": "",     # Optional credit note invoice number
                    "approveStatus": "",  # Optional status filter
                    "queryType": "1",    # 1=List all
                    "invoiceApplyCategoryCode": "",
                    "startDate": "2026-01-01",
                    "endDate": "2026-01-31",
                    "pageNo": 1,
                    "pageSize": 10
                }
        
        Returns:
            Response containing list of credit notes
        """
        # Ensure we have a valid AES key for decryption
        self.ensure_authenticated()
        
        content = json.dumps(query_params, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T112", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
            except Exception as e:
                print(f"[T112] Warning: Failed to decrypt response content: {e}")
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def stock_decrease(self, stock_data):
        """Decrease/adjust stock using T132
        
        Args:
            stock_data: Dictionary with the following structure:
                {
                    "goodsStockIn": {
                        "operationType": "101",
                        "adjustType": "101",  # 101=Loss, 102=Damage, etc.
                        "remarks": "Stock adjustment reason"
                    },
                    "goodsStockInItem": [
                        {
                            "goodsCode": "PRODUCT001",
                            "quantity": 10,
                            "unitPrice": 5000
                        }
                    ]
                }
        
        Returns:
            Response containing stock adjustment status
        """
        content = json.dumps(stock_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T132", content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        decrypted_content = self._decrypt_aes(encrypted_content)
                        result['data']['decrypted_content'] = json.loads(decrypted_content)
            except Exception as e:
                print(f"[T132] Warning: Failed to decrypt response content: {e}")
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_taxpayer_by_tin(self, tin, ninBrn=""):
        """Query taxpayer information by TIN or ninBrn using T119"""
        content = json.dumps({"tin": tin, "ninBrn": ninBrn}, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T119", content, encrypt_code=1)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_excise_duty(self, excise_duty_code=None, excise_duty_name=None):
        """Query excise duty information using T125 - Excise Duty Inquiry
        
        T125 is used to query excise duty codes and rates from EFRIS.
        This is useful for getting excise tax information for products subject to excise duty.
        
        Args:
            excise_duty_code: Optional filter by excise duty code (e.g., "LED190100")
            excise_duty_name: Optional filter by excise duty name
            
        Returns:
            Response containing list of excise duty codes and rates with details:
            {
                "returnStateInfo": {"returnCode": "00", "returnMessage": "SUCCESS"},
                "data": {
                    "content": "encrypted_data",
                    "decrypted_content": {
                        "exciseDutyList": [
                            {
                                "exciseDutyCode": "LED190100",
                                "exciseDutyName": "Excise duty name",
                                "exciseRate": "rate value",
                                "unit": "unit code",
                                "currency": "currency code",
                                ...
                            }
                        ]
                    }
                }
            }
        """
        # Ensure we have a valid AES key for decryption
        self.ensure_authenticated()
        
        # Build request content according to T125 specification
        request_content = {}
        
        # Add optional filters if provided
        if excise_duty_code:
            request_content["exciseDutyCode"] = excise_duty_code
        if excise_duty_name:
            request_content["exciseDutyName"] = excise_duty_name
            
        content = json.dumps(request_content, separators=(',', ':'), sort_keys=True)
        
        # T125 requires AES encryption (encryptCode=2)
        payload = self._build_request_payload("T125", content, encrypt_code=2)
        
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"[T125] Response status: {result.get('status')}")
            print(f"[T125] Response returnCode: {result.get('returnStateInfo', {}).get('returnCode')}")
            print(f"[T125] Response returnMessage: {result.get('returnStateInfo', {}).get('returnMessage')}")
            
            # Decrypt the response content if encrypted (encryptCode=2)
            try:
                if result.get('data', {}).get('dataDescription', {}).get('encryptCode') == '2':
                    print(f"[T125] Response is encrypted (encryptCode=2)")
                    encrypted_content = result['data']['content']
                    if encrypted_content:
                        print(f"[T125] Encrypted content length: {len(encrypted_content)}")
                        
                        # Check if content is gzip compressed
                        if encrypted_content.startswith('H4sI'):
                            print(f"[T125] Content appears to be gzip compressed")
                            # Decompress first
                            compressed_data = base64.b64decode(encrypted_content)
                            decompressed_data = gzip.decompress(compressed_data)
                            print(f"[T125] Gzip decompression successful! Decompressed size: {len(decompressed_data)}")
                            
                            # The decompressed data might still be AES encrypted
                            try:
                                # Re-encode to base64 for AES decryption
                                decompressed_b64 = base64.b64encode(decompressed_data).decode('utf-8')
                                decrypted_content = self._decrypt_aes(decompressed_b64)
                                print(f"[T125] AES decryption successful!")
                            except:
                                # If AES fails, it might be plain text
                                decrypted_content = decompressed_data.decode('utf-8')
                                print(f"[T125] Content was not encrypted, just compressed")
                        else:
                            # Try AES decryption only
                            decrypted_content = self._decrypt_aes(encrypted_content)
                            print(f"[T125] AES decryption successful!")
                        
                        print(f"[T125] Decrypted content length: {len(decrypted_content)}")
                        parsed_content = json.loads(decrypted_content)
                        print(f"[T125] Parsed content keys: {parsed_content.keys() if isinstance(parsed_content, dict) else 'not a dict'}")
                        result['data']['decrypted_content'] = parsed_content
                        print(f"[T125] Decryption successful!")
                    else:
                        print(f"[T125] No encrypted content found")
                else:
                    print(f"[T125] Response is not encrypted or encryptCode != 2")
                    print(f"[T125] encryptCode: {result.get('data', {}).get('dataDescription', {}).get('encryptCode')}")
            except Exception as e:
                print(f"[T125] Warning: Failed to decrypt response content: {e}")
                import traceback
                traceback.print_exc()
                # Return result anyway with raw content
                
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def generate_invoice(self, invoice_data):
        """Generate invoice using T109 with AES encryption
        
        This method:
        1. Converts invoice_data to JSON
        2. Encrypts with AES key (obtained from T104)
        3. Base64 encodes encrypted content
        4. RSA signs the encrypted content
        5. Sends to server
        """
        # Ensure we have the AES key
        self.ensure_authenticated()
        
        # Convert to JSON
        plain_content = json.dumps(invoice_data, separators=(',', ':'), sort_keys=True)
        
        # Build payload with AES encryption (encrypt_code=2)
        payload = self._build_request_payload("T109", plain_content, encrypt_code=2)
        
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def get_server_time(self):
        """Get server time using T10 for time synchronization"""
        content = ""
        payload = self._build_request_payload("T10", content, encrypt_code=0)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def fetch_from_quickbooks(self):
        """Placeholder for QuickBooks integration"""
        # TODO: Implement QBO API calls
        return {"message": "QuickBooks integration placeholder"}

    def _time_sync(self):
        """Perform time synchronization using T101
        
        T101 response structure:
        - data.content: Base64-encoded JSON with {currentTime}
        - data.signature: Server's signature
        """
        payload = self._build_handshake_payload("T101", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        print(f"[T101] Response status: {response.status_code}")
        print(f"[T101] Response text (first 500 chars): {response.text[:500]}")
        
        if response.status_code != 200:
            raise Exception(f"Time sync failed: {response.status_code} {response.text}")
        
        # Check if response is empty
        if not response.text or response.text.strip() == "":
            raise Exception("T101 returned empty response - EFRIS server may be down or URL incorrect")
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"T101 returned invalid JSON. Response: {response.text[:200]}")
        
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Time sync error: {data}")
        
        # Decode nested content
        content_b64 = data['data']['content']
        content_json_str = base64.b64decode(content_b64).decode('utf-8')
        content_json = json.loads(content_json_str)
        
        server_time_str = content_json['currentTime']
        print(f"[T101] Time sync successful - server time: {server_time_str}")

    def _key_exchange(self):
        """Perform key exchange using T104 to get symmetric key and signature
        
        Flow:
        1. Call T104 to get response with data.content (Base64-encoded JSON)
        2. Decode data.content to get nested JSON with passowrdDes and sign
        3. Base64 decode the passowrdDes (RSA-encrypted AES key)
        4. RSA decrypt using private key to get intermediate Base64-encoded AES key
        5. Base64 decode the decrypted value to get the actual AES key
        6. Store AES key with expiration timestamp for subsequent request encryption
        """
        payload = self._build_handshake_payload("T104", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code != 200:
            raise Exception(f"Key exchange failed: {response.status_code} {response.text}")
        data = response.json()
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Key exchange error: {data}")
        
        # T104 response structure:
        # - data.content: Base64-encoded JSON string containing {passowrdDes, sign}
        #   (Note: EFRIS has a typo - it's "passowrdDes" not "passwordDes")
        # - data.signature: Server's signature of the response
        
        # Step 1: Decode data.content from Base64 to get JSON
        content_b64 = data['data']['content']
        content_json_str = base64.b64decode(content_b64).decode('utf-8')
        content_json = json.loads(content_json_str)
        
        # Step 2: Extract passowrdDes (RSA-encrypted AES key) and sign from nested JSON
        # Note the typo in EFRIS: "passowrdDes" instead of "passwordDes"
        password_des_b64 = content_json['passowrdDes']
        self.server_sign = content_json['sign']  # Server signature value
        
        # Step 3: Base64 decode the passowrdDes (RSA-encrypted)
        password_des_encrypted = base64.b64decode(password_des_b64)
        
        # Step 4: RSA decrypt using private key to get intermediate Base64-encoded AES key
        aes_key_b64_str = self.private_key.decrypt(
            password_des_encrypted,
            padding.PKCS1v15()
        ).decode('utf-8')
        
        # Step 5: Base64 decode the decrypted value to get the actual AES key
        self.aes_key = base64.b64decode(aes_key_b64_str)
        
        # Step 6: Set expiration time for the AES key
        self.aes_key_expires_at = datetime.now() + timedelta(hours=self.key_expiry_hours)
        
        print(f"[T104] Key exchange successful!")
        print(f"       - AES key obtained: {len(self.aes_key)} bytes")
        print(f"       - Server signature length: {len(self.server_sign)}")
        print(f"       - Key expires at: {self.aes_key_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

    def is_key_valid(self):
        """Check if the current AES key is still valid (exists and not expired)"""
        if not hasattr(self, 'aes_key') or not self.aes_key:
            return False
        if not hasattr(self, 'aes_key_expires_at') or not self.aes_key_expires_at:
            return False
        return datetime.now() < self.aes_key_expires_at
    
    def ensure_valid_key(self):
        """Ensure we have a valid AES key, refresh if needed
        
        This should be called before any encrypted operation to ensure
        the AES key is available and not expired.
        """
        if not self.is_key_valid():
            print("[KEY] AES key invalid or expired, refreshing...")
            self._key_exchange()
        else:
            time_remaining = self.aes_key_expires_at - datetime.now()
            print(f"[KEY] Using cached AES key (valid for {time_remaining.total_seconds()/3600:.1f} more hours)")

    def _get_parameters(self):
        """Get parameters using T103 after successful T104 key exchange
        
        T103 response structure:
        - data.content: AES-ECB encrypted JSON (encryptCode=2)
        - data.signature: Server's RSA signature  
        - Must have AES key from T104 before calling this
        
        Note: Server uses AES-128-ECB for T103 response encryption
        """
        # Verify we have the AES key from T104
        if not self.aes_key:
            raise Exception("T103 requires AES key from T104. Call T104 first.")
        
        payload = self._build_handshake_payload("T103", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        if response.status_code != 200:
            raise Exception(f"Parameters fetch failed: {response.status_code} {response.text}")
        data = response.json()
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Parameters error: {data}")
        
        # T103 returns encrypted content (encryptCode=2)
        # Decrypt using AES-ECB (server uses ECB mode for T103 responses)
        encrypted_content_b64 = data['data']['content']
        
        # Decrypt AES-ECB
        decrypted_content = self._decrypt_aes_ecb(encrypted_content_b64)
        
        # Parse decrypted JSON
        try:
            self.registration_details = json.loads(decrypted_content)
            print(f"[T103] Parameters fetched successfully")
            print(f"       - Fields received: {len(self.registration_details)}")
        except json.JSONDecodeError as e:
            print(f"[T103] Warning: Could not parse decrypted content as JSON: {e}")
            self.registration_details = {}

    def _perform_handshake(self):
        self._time_sync()
        self._key_exchange()
        self._get_parameters()

    def ensure_authenticated(self):
        """Ensure a valid AES key is available, refreshing if necessary
        
        Checks if we have a valid (non-expired) AES key.
        If not, performs the full handshake (T101 -> T104 -> T103).
        """
        if not self.is_key_valid():
            self._perform_handshake()
        else:
            time_remaining = self.aes_key_expires_at - datetime.now()
            print(f"[AUTH] Using cached AES key (expires in {time_remaining.total_seconds()/3600:.1f} hours)")

    def perform_handshake(self):
        """Perform the mandatory handshake: time sync, key exchange, get parameters"""
        self._perform_handshake()

    def _authenticate(self):
        # Load certificate and key if provided
        if self.cert_path and self.key_path:
            with open(self.cert_path, 'rb') as cert_file:
                cert = x509.load_pem_x509_certificate(cert_file.read())
            with open(self.key_path, 'rb') as key_file:
                key = serialization.load_pem_private_key(key_file.read(), password=None)
            # For mTLS, set cert in session
            self.session = OAuth2Session(client_id=self.client_id)
            self.session.cert = (self.cert_path, self.key_path)
        else:
            self.session = OAuth2Session(client_id=self.client_id)

        # Use client_credentials flow
        response = self.session.post(
            self.token_url,
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            },
            timeout=self.request_timeout,
            verify=self.verify_ssl
        )
        if response.status_code == 200:
            self.session.token = response.json()
        else:
            raise Exception(f'Authentication failed: {response.text}')

    def _get_headers(self):
        if self.test_mode:
            return {'Content-Type': 'application/json'}
        else:
            return {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.session.token["access_token"]}'
            }

    def validate_taxpayer(self, tin):
        # Return the registration details fetched during handshake
        return self.registration_details

    def issue_receipt(self, receipt_data):
        if self.test_mode:
            payload = self._build_payload("T109", receipt_data, encrypt_code=0)  # Assume plain for now
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt'
            response = self.session.post(url, json=receipt_data, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)

    def query_receipt(self, receipt_id):
        if self.test_mode:
            data = {"receiptId": receipt_id}
            payload = self._build_payload("T110", data, encrypt_code=0)  # Assuming T110 for query
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt/{receipt_id}'
            response = self.session.get(url, headers=self._get_headers(), timeout=self.request_timeout)
            return self._handle_response(response)

    def void_receipt(self, receipt_id, void_data):
        if self.test_mode:
            data = {"receiptId": receipt_id, **void_data}
            payload = self._build_payload("T110", data, encrypt_code=0)  # Assuming T110 for void
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt/{receipt_id}/void'
            response = self.session.put(url, json=void_data, headers=self._get_headers())
            return self._handle_response(response)

    def submit_sales_report(self, report_data):
        if self.test_mode:
            payload = self._build_payload("T131", report_data, encrypt_code=0)  # Assuming T131 for report
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)
        else:
            url = f'{self.base_url}report/sales'
            response = self.session.post(url, json=report_data, headers=self._get_headers(), timeout=self.request_timeout)
            return self._handle_response(response)

    def send_purchase_order(self, po_data):
        """Submit purchase order to EFRIS using T130 - Send Purchase Order
        
        T130 is used to send purchase order information to EFRIS.
        This allows the system to track purchases and verify supplier invoices.
        
        Args:
            po_data: Dictionary containing purchase order information:
            {
                "supplierName": "Supplier name",
                "supplierTin": "supplier TIN",
                "orderNo": "PO-2024-001",
                "orderDate": "2024-01-24",
                "deliveryDate": "2024-02-15",
                "totalAmount": "500000",
                "currency": "UGX",
                "goodsDetails": [
                    {
                        "itemCode": "ITEM001",
                        "item": "Product name",
                        "qty": "10",
                        "unitPrice": "50000",
                        "total": "500000",
                        "unitOfMeasure": "102",
                        "orderNumber": "1"
                    }
                ]
            }
            
        Returns:
            Response containing purchase order submission status
        """
        self.ensure_authenticated()
        
        content = json.dumps(po_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T130", content, encrypt_code=1)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
        
        if response.status_code == 200:
            result = response.json()
            
            # Try to decrypt the content if it's encrypted
            if "data" in result and "content" in result["data"]:
                try:
                    decrypted_content = self._decrypt_aes(result["data"]["content"])
                    result["data"]["decrypted_content"] = json.loads(decrypted_content)
                except Exception as e:
                    print(f"[T130] Warning: Failed to decrypt response content: {e}")
            
            return result
        else:
            return f'API Error {response.status_code}: {response.text}'

    def register_branch(self, branch_data):
        if self.test_mode:
            payload = self._build_payload("T139", branch_data, encrypt_code=0)  # Assuming T139 for branch
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers(), timeout=self.request_timeout, verify=self.verify_ssl)
            return self._handle_response(response)


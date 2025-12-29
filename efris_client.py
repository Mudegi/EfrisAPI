import os
import json
import uuid
import base64
import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend

load_dotenv()

class EfrisManager:
    def __init__(self, tin, base_url=None, client_id=None, client_secret=None, cert_path=None, key_path=None, test_mode=False):
        self.tin = tin
        if test_mode:
            base_url = base_url or 'https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation'
            self.base_url = base_url
            self.test_mode = True
            self.session = requests.Session()
            self._load_certificate(cert_path or os.getenv('EFRIS_CERT_PATH'))
            self.registration_details = {}  # Initialize
            # self._perform_handshake()  # Commented out for now
        else:
            base_url = base_url or 'https://api.efris.ura.go.ug/efris/api/v3/'
            self.test_mode = False
            self.client_id = client_id or os.getenv('EFRIS_CLIENT_ID')
            self.client_secret = client_secret or os.getenv('EFRIS_CLIENT_SECRET')
            self.cert_path = cert_path or os.getenv('EFRIS_CERT_PATH')
            self.key_path = key_path or os.getenv('EFRIS_KEY_PATH')
            self.token_url = f'{base_url}oauth/token'
            self._authenticate()
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
        if not self.private_key:
            return ""
        data_bytes = data_str.encode('utf-8')
        signature = self.private_key.sign(data_bytes, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(signature).decode('utf-8')

    def _build_handshake_payload(self, interface_code, content):
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
            "deviceNo": "1014409555_02",
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
            "encryptCode": "1",
            "zipCode": "0"
        }
        sig = self._sign(content)
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
            "deviceNo": "1014409555_02",
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
        sig = self._sign(content)
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

    def get_registration_details(self):
        """Get registration details using T101"""
        # self.ensure_authenticated()
        content = json.dumps({"tin": self.tin}, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T103", content, encrypt_code=0)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def _encrypt_aes(self, plain_text):
        key = self.aes_key
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text.encode()) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()

    def _decrypt_aes(self, encrypted_text):
        key = self.aes_key
        data = base64.b64decode(encrypted_text)
        iv = data[:16]
        encrypted = data[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
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
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def get_goods_and_services(self, request_data):
        """Get goods and services using T123"""
        # self.ensure_authenticated()
        content = json.dumps(request_data, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T123", content, encrypt_code=1)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def query_taxpayer_by_tin(self, tin, ninBrn=""):
        """Query taxpayer information by TIN or ninBrn using T119"""
        content = json.dumps({"tin": tin, "ninBrn": ninBrn}, separators=(',', ':'), sort_keys=True)
        payload = self._build_request_payload("T119", content, encrypt_code=1)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def generate_invoice(self, invoice_data):
        """Generate invoice using T109 with AES encryption"""
        # self.ensure_authenticated()
        plain_content = json.dumps(invoice_data, separators=(',', ':'), sort_keys=True)
        encrypted_content = self._encrypt_aes(plain_content)
        payload = self._build_request_payload("T109", encrypted_content, encrypt_code=2)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def get_server_time(self):
        """Get server time using T10 for time synchronization"""
        content = ""
        payload = self._build_request_payload("T10", content, encrypt_code=0)
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return f'API Error {response.status_code}: {response.text}'

    def fetch_from_quickbooks(self):
        """Placeholder for QuickBooks integration"""
        # TODO: Implement QBO API calls
        return {"message": "QuickBooks integration placeholder"}

    def _time_sync(self):
        """Perform time synchronization using T101"""
        payload = self._build_handshake_payload("T101", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(f"Time sync failed: {response.status_code} {response.text}")
        data = response.json()
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Time sync error: {data}")
        server_time = data['data']['currentTime']  # Assume timestamp
        import time
        local_time = time.time()
        if abs(local_time - server_time) > 600:  # ±10 minutes
            raise Exception("Local time out of sync with server time")
        print("Time sync successful")

    def _key_exchange(self):
        """Perform key exchange using T104 to get symmetric key and signature"""
        payload = self._build_handshake_payload("T104", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(f"Key exchange failed: {response.status_code} {response.text}")
        data = response.json()
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Key exchange error: {data}")
        # Assuming data['data'] contains {'passwordDes': 'key_string', 'sign': 'signature'}
        self.aes_key = base64.b64decode(data['data']['passwordDes'])
        self.server_sign = data['data']['sign']  # Server signature
        print("Key exchange successful")

    def _get_parameters(self):
        payload = self._build_handshake_payload("T103", "")
        response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
        if response.status_code != 200:
            raise Exception(f"Parameters fetch failed: {response.status_code} {response.text}")
        data = response.json()
        if data.get('returnStateInfo', {}).get('returnCode') != '00':
            raise Exception(f"Parameters error: {data}")
        self.registration_details = data['data']
        print("Parameters fetch successful")

    def _perform_handshake(self):
        self._time_sync()
        self._key_exchange()
        self._get_parameters()

    def ensure_authenticated(self):
        """Ensure the client is authenticated by performing handshake if not done"""
        if not hasattr(self, 'aes_key') or self.aes_key is None:
            self._perform_handshake()

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
            }
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
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt'
            response = self.session.post(url, json=receipt_data, headers=self._get_headers())
            return self._handle_response(response)

    def query_receipt(self, receipt_id):
        if self.test_mode:
            data = {"receiptId": receipt_id}
            payload = self._build_payload("T110", data, encrypt_code=0)  # Assuming T110 for query
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt/{receipt_id}'
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)

    def void_receipt(self, receipt_id, void_data):
        if self.test_mode:
            data = {"receiptId": receipt_id, **void_data}
            payload = self._build_payload("T110", data, encrypt_code=0)  # Assuming T110 for void
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
            return self._handle_response(response)
        else:
            url = f'{self.base_url}receipt/{receipt_id}/void'
            response = self.session.put(url, json=void_data, headers=self._get_headers())
            return self._handle_response(response)

    def submit_sales_report(self, report_data):
        if self.test_mode:
            payload = self._build_payload("T131", report_data, encrypt_code=0)  # Assuming T131 for report
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
            return self._handle_response(response)
        else:
            url = f'{self.base_url}report/sales'
            response = self.session.post(url, json=report_data, headers=self._get_headers())
            return self._handle_response(response)

    def register_branch(self, branch_data):
        if self.test_mode:
            payload = self._build_payload("T139", branch_data, encrypt_code=0)  # Assuming T139 for branch
            response = self.session.post(self.base_url, json=payload, headers=self._get_headers())
            return self._handle_response(response)


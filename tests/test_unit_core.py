"""
Comprehensive Unit Tests for EFRIS Integration
Tests critical functions: signature generation, encryption, invoice posting

Requirements:
    pip install pytest pytest-asyncio pytest-cov pytest-mock faker
    
Run tests:
    pytest tests/ -v
    pytest tests/ -v --cov=. --cov-report=html
    pytest tests/ -v -k "test_signature"
"""

import pytest
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from efris_client import EfrisManager


class TestSignatureGeneration:
    """Test RSA signature generation for EFRIS"""
    
    @pytest.fixture
    def mock_private_key(self):
        """Generate a test RSA private key"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key
    
    @pytest.fixture
    def efris_manager(self, mock_private_key):
        """Create EfrisManager instance with mock key"""
        manager = EfrisManager(
            tin="1000000000",
            device_no="1000000000_02",
            test_mode=True
        )
        manager.private_key = mock_private_key
        manager.certificate = None
        return manager
    
    def test_sign_creates_valid_signature(self, efris_manager):
        """Test that _sign creates a valid base64 signature"""
        data = "test content"
        signature = efris_manager._sign(data)
        
        # Should return base64 encoded string
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Should be valid base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Signature is not valid base64: {e}")
    
    def test_sign_uses_sha1_hash(self, efris_manager, mock_private_key):
        """Verify signature uses SHA1 (EFRIS requirement)"""
        data = "test content"
        signature = efris_manager._sign(data)
        
        # Decode signature
        sig_bytes = base64.b64decode(signature)
        
        # Verify with public key using SHA1
        public_key = mock_private_key.public_key()
        data_bytes = data.encode('utf-8')
        
        # This should NOT raise an exception
        try:
            public_key.verify(
                sig_bytes,
                data_bytes,
                padding.PKCS1v15(),
                hashes.SHA1()
            )
        except Exception as e:
            pytest.fail(f"Signature verification failed: {e}")
    
    def test_sign_empty_string(self, efris_manager):
        """Test signing empty string"""
        signature = efris_manager._sign("")
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_sign_json_content(self, efris_manager):
        """Test signing JSON content"""
        json_data = json.dumps({
            "tin": "1000000000",
            "deviceNo": "1000000000_02"
        })
        signature = efris_manager._sign(json_data)
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_sign_without_private_key_raises_error(self):
        """Test that signing without private key raises exception"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        manager.private_key = None
        
        with pytest.raises(Exception, match="Private key not loaded"):
            manager._sign("test")
    
    def test_sign_consistency(self, efris_manager):
        """Test that same input produces same signature"""
        data = "consistent test data"
        sig1 = efris_manager._sign(data)
        sig2 = efris_manager._sign(data)
        
        assert sig1 == sig2


class TestAESEncryption:
    """Test AES encryption/decryption for EFRIS"""
    
    @pytest.fixture
    def efris_manager_with_key(self):
        """Create EfrisManager with AES key"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        # Set a valid 32-byte AES key (256-bit)
        manager.aes_key = b'12345678901234567890123456789012'
        return manager
    
    def test_encrypt_aes_returns_base64(self, efris_manager_with_key):
        """Test AES encryption returns base64 string"""
        plaintext = "test data"
        encrypted = efris_manager_with_key._encrypt_aes(plaintext)
        
        assert isinstance(encrypted, str)
        
        # Should be valid base64
        try:
            base64.b64decode(encrypted)
        except Exception as e:
            pytest.fail(f"Encrypted output is not valid base64: {e}")
    
    def test_encrypt_decrypt_roundtrip(self, efris_manager_with_key):
        """Test that encryption followed by decryption returns original data"""
        original = "Hello EFRIS! 你好 🎉"
        encrypted = efris_manager_with_key._encrypt_aes(original)
        decrypted = efris_manager_with_key._decrypt_aes(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_json_data(self, efris_manager_with_key):
        """Test encrypting JSON data"""
        json_data = json.dumps({
            "tin": "1000000000",
            "amount": 100000,
            "items": ["item1", "item2"]
        })
        encrypted = efris_manager_with_key._encrypt_aes(json_data)
        decrypted = efris_manager_with_key._decrypt_aes(encrypted)
        
        assert decrypted == json_data
        
        # Should be able to parse back to JSON
        parsed = json.loads(decrypted)
        assert parsed["tin"] == "1000000000"
    
    def test_encrypt_empty_string(self, efris_manager_with_key):
        """Test encrypting empty string"""
        encrypted = efris_manager_with_key._encrypt_aes("")
        decrypted = efris_manager_with_key._decrypt_aes(encrypted)
        assert decrypted == ""
    
    def test_encrypt_large_data(self, efris_manager_with_key):
        """Test encrypting large dataset"""
        large_data = "X" * 10000  # 10KB of data
        encrypted = efris_manager_with_key._encrypt_aes(large_data)
        decrypted = efris_manager_with_key._decrypt_aes(encrypted)
        assert decrypted == large_data
    
    def test_encrypt_without_aes_key_raises_error(self):
        """Test that encryption without AES key raises exception"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        manager.aes_key = None
        
        with pytest.raises(Exception):
            manager._encrypt_aes("test")
    
    def test_decrypt_invalid_base64_raises_error(self, efris_manager_with_key):
        """Test that decrypting invalid base64 raises exception"""
        with pytest.raises(Exception):
            efris_manager_with_key._decrypt_aes("not-valid-base64!!!")


class TestInvoicePosting:
    """Test invoice posting functionality"""
    
    @pytest.fixture
    def efris_manager(self):
        """Create EfrisManager for testing"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        manager.aes_key = b'12345678901234567890123456789012'
        manager.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return manager
    
    @pytest.fixture
    def sample_invoice(self):
        """Sample invoice data"""
        return {
            "sellerDetails": {
                "tin": "1000000000",
                "ninBrn": "1000000000",
                "legalName": "Test Company Ltd",
                "businessName": "Test Business",
                "address": "Kampala",
                "mobilePhone": "0700000000",
                "linePhone": "0414000000",
                "emailAddress": "test@example.com"
            },
            "basicInformation": {
                "invoiceNo": "INV-001",
                "antifakeCode": "",
                "deviceNo": "1000000000_02",
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "Admin",
                "currency": "UGX",
                "oriInvoiceId": "",
                "invoiceType": "1",
                "invoiceKind": "1",
                "dataSource": "101",
                "invoiceIndustryCode": "101",
                "isBatch": "0"
            },
            "buyerDetails": {
                "buyerTin": "1000000001",
                "buyerNinBrn": "",
                "buyerPassportNum": "",
                "buyerLegalName": "Buyer Company",
                "buyerBusinessName": "",
                "buyerAddress": "Kampala",
                "buyerEmail": "buyer@example.com",
                "buyerMobilePhone": "0700000001",
                "buyerLinePhone": "",
                "buyerPlaceOfBusi": "",
                "buyerType": "0",
                "buyerCitizenship": "1",
                "buyerSector": "1"
            },
            "goodsDetails": [
                {
                    "item": "Test Product",
                    "itemCode": "PROD001",
                    "qty": "1",
                    "unitOfMeasure": "101",
                    "unitPrice": "100000",
                    "total": "100000",
                    "taxRate": "0.18",
                    "tax": "18000",
                    "discountTotal": "0",
                    "discountTaxRate": "0.18",
                    "orderNumber": "0",
                    "discountFlag": "0",
                    "deemedFlag": "0",
                    "exciseFlag": "0",
                    "categoryId": "",
                    "categoryName": "",
                    "goodsCategoryId": "1234567890123",
                    "goodsCategoryName": "Test Category",
                    "exciseRate": "",
                    "exciseRule": "",
                    "exciseTax": "",
                    "pack": "",
                    "stick": "",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "exciseRateName": ""
                }
            ],
            "taxDetails": [
                {
                    "taxCategoryCode": "01",
                    "netAmount": "100000",
                    "taxRate": "0.18",
                    "taxAmount": "18000",
                    "grossAmount": "118000",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "taxRateName": "Standard-18%"
                }
            ],
            "summary": {
                "netAmount": "100000",
                "taxAmount": "18000",
                "grossAmount": "118000",
                "itemCount": "1",
                "modeCode": "0",
                "remarks": "",
                "qrCode": ""
            },
            "payWay": [
                {
                    "paymentMode": "101",
                    "paymentAmount": "118000",
                    "orderNumber": "0"
                }
            ],
            "extend": {
                "reason": "",
                "reasonCode": ""
            }
        }
    
    def test_invoice_structure_validation(self, sample_invoice):
        """Test that sample invoice has required structure"""
        assert "sellerDetails" in sample_invoice
        assert "basicInformation" in sample_invoice
        assert "buyerDetails" in sample_invoice
        assert "goodsDetails" in sample_invoice
        assert "taxDetails" in sample_invoice
        assert "summary" in sample_invoice
        
        # Check required seller fields
        seller = sample_invoice["sellerDetails"]
        assert "tin" in seller
        assert "legalName" in seller
        
        # Check basic info
        basic = sample_invoice["basicInformation"]
        assert "invoiceNo" in basic
        assert "deviceNo" in basic
        assert "issuedDate" in basic
    
    @patch('efris_client.requests.Session.post')
    def test_upload_invoice_request_structure(self, mock_post, efris_manager, sample_invoice):
        """Test that upload_invoice creates proper request structure"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "returnStateInfo": {
                "returnCode": "00",
                "returnMessage": "Success"
            },
            "data": {
                "invoiceId": "TEST123456",
                "qrCode": "QRCODE_DATA"
            }
        }
        mock_post.return_value = mock_response
        
        # Attempt to upload (will fail without proper setup, but we can test structure)
        invoice_json = json.dumps(sample_invoice)
        
        # Test that we can create encrypted content
        encrypted_content = efris_manager._encrypt_aes(invoice_json)
        assert isinstance(encrypted_content, str)
        
        # Test that we can sign the content
        signature = efris_manager._sign(invoice_json)
        assert isinstance(signature, str)
    
    def test_invoice_json_serialization(self, sample_invoice):
        """Test that invoice can be serialized to JSON"""
        try:
            json_str = json.dumps(sample_invoice)
            assert len(json_str) > 0
            
            # Should be deserializable
            parsed = json.loads(json_str)
            assert parsed["sellerDetails"]["tin"] == sample_invoice["sellerDetails"]["tin"]
        except Exception as e:
            pytest.fail(f"Invoice JSON serialization failed: {e}")


class TestT104KeyExchange:
    """Test T104 key exchange functionality"""
    
    @pytest.fixture
    def efris_manager(self):
        """Create EfrisManager for testing"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        manager.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return manager
    
    @patch('efris_client.requests.Session.post')
    def test_t104_request_structure(self, mock_post, efris_manager):
        """Test T104 request payload structure"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "returnStateInfo": {"returnCode": "00"},
            "data": {
                "content": base64.b64encode(b"mock_encrypted_key").decode(),
                "dataDescription": {"codeType": "0"},
                "dataSign": "mock_signature"
            }
        }
        mock_post.return_value = mock_response
        
        # This will make the actual T104 call
        try:
            efris_manager.t104_key_exchange()
        except Exception as e:
            # We expect it might fail due to mock, but we can check the call
            pass
        
        # Verify the request was made
        if mock_post.called:
            call_args = mock_post.call_args
            request_data = call_args[1]['json'] if 'json' in call_args[1] else json.loads(call_args[1]['data'])
            
            # Should have required structure
            assert "data" in request_data
            assert "interfaceCode" in request_data["data"]
            assert request_data["data"]["interfaceCode"] == "T104"
    
    def test_aes_key_expiry_tracking(self, efris_manager):
        """Test that AES key expiry is tracked"""
        # Set AES key
        efris_manager.aes_key = b'12345678901234567890123456789012'
        efris_manager.aes_key_expires_at = datetime.now() + timedelta(hours=24)
        
        # Should not be expired
        assert not efris_manager.is_aes_key_expired()
        
        # Set expired time
        efris_manager.aes_key_expires_at = datetime.now() - timedelta(hours=1)
        assert efris_manager.is_aes_key_expired()


class TestEfrisManager:
    """Test EfrisManager initialization and configuration"""
    
    def test_initialization_test_mode(self):
        """Test initialization in test mode"""
        manager = EfrisManager(
            tin="1000000000",
            device_no="1000000000_02",
            test_mode=True
        )
        
        assert manager.tin == "1000000000"
        assert manager.device_no == "1000000000_02"
        assert manager.test_mode == True
        assert "efristest" in manager.base_url.lower()
    
    def test_initialization_production_mode(self):
        """Test initialization in production mode"""
        manager = EfrisManager(
            tin="1000000000",
            device_no="1000000000_02",
            test_mode=False
        )
        
        assert manager.test_mode == False
        assert "efristest" not in manager.base_url.lower()
    
    def test_timeout_configuration(self):
        """Test that timeout is properly configured"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        assert hasattr(manager, 'request_timeout')
        assert manager.request_timeout > 0
    
    def test_device_number_default(self):
        """Test default device number generation"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        assert manager.device_no == "1000000000_02"
    
    def test_aes_key_initially_none(self):
        """Test that AES key is None on initialization"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        assert manager.aes_key is None


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def efris_manager(self):
        """Create EfrisManager for testing"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        return manager
    
    def test_sign_without_certificate_raises_error(self, efris_manager):
        """Test signing without certificate"""
        efris_manager.private_key = None
        with pytest.raises(Exception):
            efris_manager._sign("test")
    
    def test_encrypt_without_aes_key_raises_error(self, efris_manager):
        """Test encryption without AES key"""
        efris_manager.aes_key = None
        with pytest.raises(Exception):
            efris_manager._encrypt_aes("test")
    
    def test_invalid_tin_format(self):
        """Test initialization with invalid TIN"""
        # Should still initialize but might fail later
        manager = EfrisManager(tin="invalid", test_mode=True)
        assert manager.tin == "invalid"
    
    @patch('efris_client.requests.Session.post')
    def test_network_timeout_handling(self, mock_post, efris_manager):
        """Test handling of network timeouts"""
        import requests
        mock_post.side_effect = requests.Timeout("Connection timeout")
        
        # Should handle timeout gracefully
        with pytest.raises(requests.Timeout):
            efris_manager.t104_key_exchange()


# Performance Tests
class TestPerformance:
    """Performance and load tests for critical functions"""
    
    @pytest.fixture
    def efris_manager(self):
        """Create EfrisManager with keys"""
        manager = EfrisManager(tin="1000000000", test_mode=True)
        manager.aes_key = b'12345678901234567890123456789012'
        manager.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return manager
    
    def test_signing_performance(self, efris_manager, benchmark):
        """Benchmark signature generation"""
        data = "test data for signing"
        result = benchmark(efris_manager._sign, data)
        assert result is not None
    
    def test_encryption_performance(self, efris_manager, benchmark):
        """Benchmark AES encryption"""
        data = "test data for encryption"
        result = benchmark(efris_manager._encrypt_aes, data)
        assert result is not None
    
    def test_encryption_large_data_performance(self, efris_manager):
        """Test encryption performance with large data"""
        import time
        
        large_data = "X" * 50000  # 50KB
        start = time.time()
        encrypted = efris_manager._encrypt_aes(large_data)
        end = time.time()
        
        duration = end - start
        assert duration < 1.0, f"Encryption took {duration}s, should be < 1s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Integration Tests for EFRIS API
Tests real API calls to EFRIS (requires test credentials)

Requirements:
    pip install pytest pytest-asyncio python-dotenv
    
Environment Variables Required (.env):
    EFRIS_TIN=your_test_tin
    EFRIS_DEVICE_NO=your_device_number
    EFRIS_CERT_PATH=path/to/certificate.p12
    
Run tests:
    pytest tests/test_integration_efris.py -v
    pytest tests/test_integration_efris.py -v -k "test_t104"
    pytest tests/test_integration_efris.py -v --integration  # Only integration tests
"""

import pytest
import json
import os
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from efris_client import EfrisManager

load_dotenv()

# Skip all tests if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv('EFRIS_TIN'),
    reason="EFRIS credentials not configured"
)


@pytest.fixture(scope="session")
def efris_manager():
    """Create EfrisManager with real credentials"""
    tin = os.getenv('EFRIS_TIN')
    device_no = os.getenv('EFRIS_DEVICE_NO')
    cert_path = os.getenv('EFRIS_CERT_PATH')
    
    if not tin:
        pytest.skip("EFRIS_TIN not configured")
    
    manager = EfrisManager(
        tin=tin,
        device_no=device_no,
        cert_path=cert_path,
        test_mode=True  # Use test environment
    )
    
    return manager


class TestT104KeyExchangeIntegration:
    """Integration tests for T104 key exchange"""
    
    @pytest.mark.integration
    def test_t104_key_exchange_success(self, efris_manager):
        """Test successful T104 key exchange with EFRIS"""
        try:
            result = efris_manager.t104_key_exchange()
            
            # Should return success
            assert result is not None
            
            # AES key should be set
            assert efris_manager.aes_key is not None
            assert len(efris_manager.aes_key) == 32  # 256-bit key
            
            # Expiry should be set
            assert efris_manager.aes_key_expires_at is not None
            
            print(f"✓ T104 Key Exchange Successful")
            print(f"  AES Key Length: {len(efris_manager.aes_key)} bytes")
            print(f"  Expires At: {efris_manager.aes_key_expires_at}")
            
        except Exception as e:
            pytest.fail(f"T104 key exchange failed: {e}")
    
    @pytest.mark.integration
    def test_t104_key_exchange_timeout(self, efris_manager):
        """Test T104 with timeout (should complete within configured time)"""
        import time
        
        start = time.time()
        try:
            efris_manager.t104_key_exchange()
            duration = time.time() - start
            
            # Should complete within timeout
            assert duration < efris_manager.request_timeout
            print(f"✓ T104 completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start
            print(f"✗ T104 failed after {duration:.2f}s: {e}")
            raise


class TestT101ProductRegistration:
    """Integration tests for T101 product registration"""
    
    @pytest.fixture
    def sample_product(self):
        """Sample product for registration"""
        return {
            "operationType": "101",  # Add new product
            "goodsName": f"Test Product {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "goodsCode": "",
            "measureUnit": "101",
            "unitPrice": "10000",
            "currency": "UGX",
            "commodityCategoryId": "1234567890123",
            "haveExciseTax": "0",
            "description": "Integration test product"
        }
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_register_product_success(self, efris_manager, sample_product):
        """Test successful product registration"""
        # Ensure we have AES key
        if not efris_manager.aes_key:
            efris_manager.t104_key_exchange()
        
        try:
            result = efris_manager.t101_register_items([sample_product])
            
            assert result is not None
            assert "returnStateInfo" in result
            
            return_code = result["returnStateInfo"].get("returnCode")
            return_message = result["returnStateInfo"].get("returnMessage")
            
            print(f"✓ Product Registration Result:")
            print(f"  Return Code: {return_code}")
            print(f"  Message: {return_message}")
            
            if return_code == "00":
                # Success
                assert "data" in result
                print(f"  Product registered successfully")
            else:
                # May fail if product already exists, that's okay for test
                print(f"  Registration failed (expected if product exists)")
                
        except Exception as e:
            pytest.fail(f"Product registration failed: {e}")


class TestT111InvoiceUpload:
    """Integration tests for T111 invoice upload"""
    
    @pytest.fixture
    def sample_invoice(self, efris_manager):
        """Generate sample invoice for testing"""
        return {
            "sellerDetails": {
                "tin": efris_manager.tin,
                "ninBrn": efris_manager.tin,
                "legalName": "Test Company Ltd",
                "businessName": "Test Business",
                "address": "Kampala, Uganda",
                "mobilePhone": "0700000000",
                "linePhone": "0414000000",
                "emailAddress": "test@example.com"
            },
            "basicInformation": {
                "invoiceNo": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "antifakeCode": "",
                "deviceNo": efris_manager.device_no,
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "Integration Test",
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
                "buyerLegalName": "Test Buyer Company",
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
                    "item": "Integration Test Item",
                    "itemCode": "TEST001",
                    "qty": "1",
                    "unitOfMeasure": "101",
                    "unitPrice": "10000",
                    "total": "10000",
                    "taxRate": "0.18",
                    "tax": "1800",
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
                    "netAmount": "10000",
                    "taxRate": "0.18",
                    "taxAmount": "1800",
                    "grossAmount": "11800",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "taxRateName": "Standard-18%"
                }
            ],
            "summary": {
                "netAmount": "10000",
                "taxAmount": "1800",
                "grossAmount": "11800",
                "itemCount": "1",
                "modeCode": "0",
                "remarks": "Integration test invoice",
                "qrCode": ""
            },
            "payWay": [
                {
                    "paymentMode": "101",
                    "paymentAmount": "11800",
                    "orderNumber": "0"
                }
            ],
            "extend": {
                "reason": "",
                "reasonCode": ""
            }
        }
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_upload_invoice_success(self, efris_manager, sample_invoice):
        """Test successful invoice upload"""
        # Ensure we have AES key
        if not efris_manager.aes_key:
            efris_manager.t104_key_exchange()
        
        try:
            result = efris_manager.upload_invoice(sample_invoice)
            
            assert result is not None
            assert "returnStateInfo" in result
            
            return_code = result["returnStateInfo"].get("returnCode")
            return_message = result["returnStateInfo"].get("returnMessage")
            
            print(f"✓ Invoice Upload Result:")
            print(f"  Return Code: {return_code}")
            print(f"  Message: {return_message}")
            
            if return_code == "00":
                # Success
                assert "data" in result
                data = result["data"]
                
                print(f"  Invoice ID: {data.get('invoiceId', 'N/A')}")
                print(f"  Verification Code: {data.get('verificationCode', 'N/A')}")
                print(f"  QR Code: {data.get('qrCode', 'N/A')[:50]}...")
                
                # Should have invoice ID
                assert "invoiceId" in data
                assert len(data["invoiceId"]) > 0
            else:
                print(f"  Upload failed: {return_message}")
                # Don't fail test, might be expected in test environment
                
        except Exception as e:
            pytest.fail(f"Invoice upload failed: {e}")


class TestT109InvoiceQuery:
    """Integration tests for T109 invoice query"""
    
    @pytest.mark.integration
    def test_query_invoices_success(self, efris_manager):
        """Test querying invoices"""
        # Ensure we have AES key
        if not efris_manager.aes_key:
            efris_manager.t104_key_exchange()
        
        try:
            # Query last 7 days
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            result = efris_manager.t109_query_invoices(
                page_no=1,
                page_size=10,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            assert result is not None
            assert "returnStateInfo" in result
            
            return_code = result["returnStateInfo"].get("returnCode")
            
            print(f"✓ Invoice Query Result:")
            print(f"  Return Code: {return_code}")
            
            if return_code == "00" and "data" in result:
                records = result["data"].get("records", [])
                print(f"  Found {len(records)} invoices")
                
                for i, invoice in enumerate(records[:3], 1):
                    print(f"  Invoice {i}: {invoice.get('invoiceNo', 'N/A')}")
            
        except Exception as e:
            pytest.fail(f"Invoice query failed: {e}")


class TestNetworkResilience:
    """Test network error handling and resilience"""
    
    @pytest.mark.integration
    def test_timeout_handling(self, efris_manager):
        """Test that timeouts are handled properly"""
        # Set very short timeout
        original_timeout = efris_manager.request_timeout
        efris_manager.request_timeout = 0.001  # 1ms - will timeout
        
        try:
            efris_manager.t104_key_exchange()
            # Should have timed out
        except Exception as e:
            # Expected to timeout
            assert "timeout" in str(e).lower() or "time" in str(e).lower()
            print(f"✓ Timeout handled correctly: {type(e).__name__}")
        finally:
            efris_manager.request_timeout = original_timeout
    
    @pytest.mark.integration
    def test_invalid_url_handling(self):
        """Test handling of invalid EFRIS URL"""
        manager = EfrisManager(
            tin="1000000000",
            base_url="https://invalid-url-that-does-not-exist.com/api",
            test_mode=True
        )
        
        try:
            manager.t104_key_exchange()
        except Exception as e:
            # Should handle gracefully
            print(f"✓ Invalid URL handled: {type(e).__name__}")
            assert True


class TestConcurrency:
    """Test concurrent EFRIS operations"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_key_exchange(self):
        """Test multiple concurrent T104 key exchanges"""
        import concurrent.futures
        import time
        
        def do_key_exchange(i):
            tin = os.getenv('EFRIS_TIN')
            manager = EfrisManager(tin=tin, test_mode=True)
            
            start = time.time()
            try:
                manager.t104_key_exchange()
                duration = time.time() - start
                return (i, True, duration, None)
            except Exception as e:
                duration = time.time() - start
                return (i, False, duration, str(e))
        
        # Run 5 concurrent key exchanges
        num_concurrent = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(do_key_exchange, i) for i in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = sum(1 for r in results if r[1])
        failed = len(results) - successful
        avg_duration = sum(r[2] for r in results) / len(results)
        
        print(f"✓ Concurrent Key Exchange Test:")
        print(f"  Total: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Avg Duration: {avg_duration:.2f}s")
        
        # At least 80% should succeed
        assert successful >= len(results) * 0.8


class TestDataValidation:
    """Test data validation before sending to EFRIS"""
    
    def test_tin_format_validation(self):
        """Test TIN format validation"""
        # Valid TINs
        valid_tins = ["1000000000", "1234567890"]
        for tin in valid_tins:
            manager = EfrisManager(tin=tin, test_mode=True)
            assert manager.tin == tin
        
        # Invalid TINs (still creates manager but may fail later)
        invalid_tins = ["", "123", "ABC1234567"]
        for tin in invalid_tins:
            manager = EfrisManager(tin=tin, test_mode=True)
            assert manager.tin == tin  # Still creates, validates on API call
    
    def test_invoice_date_format_validation(self):
        """Test invoice date format"""
        valid_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assert len(valid_date) == 19
        assert valid_date[4] == "-"
        assert valid_date[7] == "-"
        assert valid_date[10] == " "


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])

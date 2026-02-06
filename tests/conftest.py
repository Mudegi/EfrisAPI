"""
Shared pytest fixtures and test utilities

This file contains reusable fixtures, test data generators,
and helper functions used across all test files.
"""

import pytest
import os
from datetime import datetime, timedelta
from faker import Faker
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from efris_client import EfrisManager

# Initialize Faker for generating random test data
fake = Faker()


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from environment"""
    return {
        "tin": os.getenv("EFRIS_TIN", "1000000000"),
        "device_no": os.getenv("EFRIS_DEVICE_NO", "1000000000_02"),
        "cert_path": os.getenv("EFRIS_CERT_PATH", ""),
        "test_mode": os.getenv("EFRIS_USE_TEST_MODE", "true").lower() == "true"
    }


@pytest.fixture(scope="session")
def has_credentials(test_config):
    """Check if EFRIS credentials are configured"""
    return (
        test_config["tin"] != "1000000000" and
        test_config["cert_path"] and
        os.path.exists(test_config["cert_path"])
    )


# ============================================================================
# EFRIS MANAGER FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def efris_manager_session(test_config):
    """
    Session-scoped EfrisManager for integration tests
    Reuses same instance across tests to avoid repeated key exchanges
    """
    if test_config["cert_path"] and os.path.exists(test_config["cert_path"]):
        manager = EfrisManager(
            tin=test_config["tin"],
            device_no=test_config["device_no"],
            cert_path=test_config["cert_path"],
            test_mode=test_config["test_mode"]
        )
        return manager
    return None


@pytest.fixture
def efris_manager(test_config):
    """
    Function-scoped EfrisManager for unit tests
    Creates new instance for each test
    """
    manager = EfrisManager(
        tin=test_config["tin"],
        device_no=test_config["device_no"],
        test_mode=True
    )
    return manager


# ============================================================================
# CRYPTOGRAPHY FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_private_key():
    """Generate a test RSA private key (2048-bit)"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return private_key


@pytest.fixture(scope="session")
def test_public_key(test_private_key):
    """Get public key from test private key"""
    return test_private_key.public_key()


@pytest.fixture(scope="session")
def test_aes_key():
    """Generate a test AES-256 key (32 bytes)"""
    return os.urandom(32)


@pytest.fixture
def mock_certificate_path(tmp_path):
    """Create a temporary mock certificate path"""
    cert_file = tmp_path / "test_cert.p12"
    cert_file.write_bytes(b"MOCK_CERTIFICATE_DATA")
    return str(cert_file)


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

@pytest.fixture
def generate_tin():
    """Generate random TIN (10 digits)"""
    def _generate():
        return str(fake.random_int(min=1000000000, max=9999999999))
    return _generate


@pytest.fixture
def generate_invoice_number():
    """Generate unique invoice number with timestamp"""
    def _generate(prefix="TEST"):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = fake.random_int(min=1000, max=9999)
        return f"{prefix}-{timestamp}-{random_suffix}"
    return _generate


@pytest.fixture
def generate_company_data():
    """Generate fake company data"""
    def _generate():
        return {
            "company_name": fake.company(),
            "tin": str(fake.random_int(min=1000000000, max=9999999999)),
            "legal_name": fake.company(),
            "address": fake.address()[:50],
            "email": fake.company_email(),
            "phone": fake.phone_number()[:15],
            "contact_person": fake.name()
        }
    return _generate


@pytest.fixture
def generate_product_data():
    """Generate fake product data"""
    def _generate():
        unit_price = fake.random_int(min=1000, max=100000)
        qty = fake.random_int(min=1, max=10)
        total = unit_price * qty
        tax = int(total * 0.18)
        
        return {
            "item": fake.word().capitalize(),
            "itemCode": f"ITEM{fake.random_int(min=100, max=999)}",
            "qty": str(qty),
            "unitOfMeasure": "101",
            "unitPrice": str(unit_price),
            "total": str(total),
            "taxRate": "0.18",
            "tax": str(tax),
            "goodsCategoryId": "1234567890123",
            "commodityCategoryId": "1010101010"
        }
    return _generate


@pytest.fixture
def generate_invoice_data(generate_company_data, generate_product_data, generate_invoice_number):
    """Generate complete invoice data structure"""
    def _generate(num_items=1):
        seller = generate_company_data()
        buyer = generate_company_data()
        invoice_no = generate_invoice_number()
        
        # Generate products
        products = [generate_product_data() for _ in range(num_items)]
        
        # Calculate totals
        net_amount = sum(int(p["total"]) for p in products)
        tax_amount = sum(int(p["tax"]) for p in products)
        gross_amount = net_amount + tax_amount
        
        return {
            "sellerDetails": {
                "tin": seller["tin"],
                "legalName": seller["legal_name"],
                "businessName": seller["company_name"],
                "address": seller["address"],
                "mobilePhone": seller["phone"],
                "emailAddress": seller["email"]
            },
            "basicInformation": {
                "invoiceNo": invoice_no,
                "deviceNo": "1000000000_02",
                "issuedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "TestOperator",
                "currency": "UGX",
                "invoiceType": "1",  # Normal invoice
                "invoiceKind": "1",  # Original invoice
                "dataSource": "101",  # Self-developed
                "invoiceIndustryCode": "101"  # General
            },
            "buyerDetails": {
                "buyerTin": buyer["tin"],
                "buyerLegalName": buyer["legal_name"],
                "buyerBusinessName": buyer["company_name"],
                "buyerAddress": buyer["address"],
                "buyerMobilePhone": buyer["phone"],
                "buyerEmail": buyer["email"],
                "buyerType": "1"  # General taxpayer
            },
            "goodsDetails": products,
            "summary": {
                "netAmount": str(net_amount),
                "taxAmount": str(tax_amount),
                "grossAmount": str(gross_amount),
                "itemCount": str(num_items),
                "modeCode": "0"  # General mode
            },
            "payWay": [{
                "paymentMode": "101",  # Cash
                "paymentAmount": str(gross_amount)
            }]
        }
    return _generate


# ============================================================================
# DATE/TIME FIXTURES
# ============================================================================

@pytest.fixture
def today():
    """Get today's date in EFRIS format"""
    return datetime.now().strftime("%Y-%m-%d")


@pytest.fixture
def now():
    """Get current datetime in EFRIS format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@pytest.fixture
def date_range():
    """Generate date range for queries"""
    def _generate(days_ago=7):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_ago)
        return {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }
    return _generate


# ============================================================================
# MOCK API RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
def mock_success_response():
    """Mock successful EFRIS API response"""
    return {
        "returnStateInfo": {
            "returnCode": "00",
            "returnMessage": "SUCCESS"
        },
        "data": {}
    }


@pytest.fixture
def mock_error_response():
    """Mock error EFRIS API response"""
    return {
        "returnStateInfo": {
            "returnCode": "01",
            "returnMessage": "ERROR"
        }
    }


@pytest.fixture
def mock_t104_response(test_aes_key):
    """Mock T104 key exchange response"""
    import base64
    return {
        "returnStateInfo": {
            "returnCode": "00",
            "returnMessage": "SUCCESS"
        },
        "data": {
            "content": base64.b64encode(test_aes_key).decode('utf-8')
        }
    }


@pytest.fixture
def mock_t111_response():
    """Mock T111 invoice upload response"""
    return {
        "returnStateInfo": {
            "returnCode": "00",
            "returnMessage": "SUCCESS"
        },
        "data": {
            "invoiceId": fake.uuid4(),
            "invoiceNo": f"TEST-{int(datetime.now().timestamp())}",
            "verificationCode": fake.random_int(min=100000, max=999999),
            "qrCode": f"https://efris.example.com/qr/{fake.uuid4()}"
        }
    }


# ============================================================================
# PERFORMANCE MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires EFRIS credentials)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (may take > 10 seconds)"
    )
    config.addinivalue_line(
        "markers", "load: Load/stress tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmarks"
    )


# ============================================================================
# TEST SESSION HOOKS
# ============================================================================

def pytest_sessionstart(session):
    """Called before test run starts"""
    print("\n" + "="*60)
    print("🧪 EFRIS API Test Suite")
    print("="*60)
    
    # Check environment
    has_creds = os.getenv("EFRIS_TIN") and os.getenv("EFRIS_CERT_PATH")
    print(f"Test Mode: {'ENABLED' if os.getenv('EFRIS_USE_TEST_MODE', 'true') == 'true' else 'DISABLED'}")
    print(f"Integration Tests: {'ENABLED' if has_creds else 'DISABLED (missing credentials)'}")
    print("="*60 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Called after test run finishes"""
    print("\n" + "="*60)
    print("✅ Test Suite Completed")
    print(f"Exit Status: {exitstatus}")
    print("="*60 + "\n")


# ============================================================================
# TEST REPORT HOOKS
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add extra information to test reports"""
    outcome = yield
    report = outcome.get_result()
    
    # Add test duration to report
    if report.when == "call":
        report.duration_ms = report.duration * 1000
        
        # Flag slow tests
        if report.duration > 10:
            report.slow_test = True


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture
def cleanup_test_invoices():
    """Cleanup test invoices after test"""
    created_invoices = []
    
    yield created_invoices
    
    # Cleanup logic here (if needed)
    for invoice_id in created_invoices:
        print(f"Cleaning up invoice: {invoice_id}")
        # Add cleanup code


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def assert_valid_response(response):
    """Helper to validate EFRIS API response structure"""
    assert "returnStateInfo" in response
    assert "returnCode" in response["returnStateInfo"]
    assert response["returnStateInfo"]["returnCode"] == "00"


def assert_valid_signature(signature):
    """Helper to validate signature format"""
    import base64
    assert signature is not None
    assert len(signature) > 0
    # Should be valid base64
    decoded = base64.b64decode(signature)
    assert len(decoded) > 0


def assert_valid_invoice(invoice_data):
    """Helper to validate invoice structure"""
    required_keys = ["sellerDetails", "basicInformation", "buyerDetails", "goodsDetails", "summary"]
    for key in required_keys:
        assert key in invoice_data, f"Missing required key: {key}"
    
    # Validate invoice number
    assert "invoiceNo" in invoice_data["basicInformation"]
    assert len(invoice_data["basicInformation"]["invoiceNo"]) > 0
    
    # Validate at least one product
    assert len(invoice_data["goodsDetails"]) > 0


# Make utilities available to all tests
pytest.assert_valid_response = assert_valid_response
pytest.assert_valid_signature = assert_valid_signature
pytest.assert_valid_invoice = assert_valid_invoice

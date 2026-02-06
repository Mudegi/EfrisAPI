# 🧪 EFRIS API Testing Guide

Complete guide to testing the EFRIS API integration system.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Types](#test-types)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Troubleshooting](#troubleshooting)
7. [Performance Targets](#performance-targets)

---

## 🚀 Quick Start

### Installation

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock faker

# Install load testing tools
pip install locust

# Install code quality tools (optional)
pip install black flake8 mypy pylint isort
```

### Run All Tests

```bash
# Run everything (unit tests only by default)
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html

# Open coverage report
start htmlcov/index.html   # Windows
open htmlcov/index.html    # Mac
```

---

## 🧩 Test Types

### 1. Unit Tests (`test_unit_core.py`)

**Purpose**: Test individual functions in isolation

**Characteristics**:
- ⚡ Fast (< 1 second each)
- 🔒 No external dependencies
- 🎭 Uses mocks for external APIs
- 🎯 Tests single responsibility

**Coverage**:
- ✅ RSA signature generation (SHA1 with PKCS1v15)
- ✅ AES-256 encryption/decryption
- ✅ Invoice structure validation
- ✅ T104 key exchange logic
- ✅ Error handling
- ✅ Performance benchmarks

**Run Command**:
```bash
pytest tests/test_unit_core.py -v
```

**Example Test**:
```python
def test_sign_creates_valid_signature(efris_manager, test_private_key):
    """Test that signature generation produces valid base64 output"""
    efris_manager.private_key = test_private_key
    content = "test content"
    
    signature = efris_manager.sign(content)
    
    assert signature is not None
    assert len(signature) > 0
    # Verify it's valid base64
    import base64
    decoded = base64.b64decode(signature)
    assert len(decoded) == 256  # 2048-bit key produces 256-byte signature
```

---

### 2. Integration Tests (`test_integration_efris.py`)

**Purpose**: Test real EFRIS API interactions

**Characteristics**:
- 🐢 Slower (network calls required)
- 🌐 Requires EFRIS test credentials
- 🔗 Tests end-to-end workflows
- ✅ Validates actual API responses

**Coverage**:
- ✅ T104 key exchange (real API)
- ✅ T101 product registration
- ✅ T111 invoice submission
- ✅ T109 invoice queries
- ✅ Network error handling
- ✅ Concurrent API calls (5 threads)

**Setup Required**:

Create `.env` file:
```env
EFRIS_TIN=your_test_tin
EFRIS_DEVICE_NO=your_device_number
EFRIS_CERT_PATH=path/to/certificate.p12
EFRIS_USE_TEST_MODE=true
```

**Run Command**:
```bash
# Run integration tests (requires credentials)
pytest tests/test_integration_efris.py -v -m integration

# Run with detailed output
pytest tests/test_integration_efris.py -v -m integration -s
```

**Example Test**:
```python
@pytest.mark.integration
def test_t104_key_exchange_success(efris_manager):
    """Test real T104 key exchange with EFRIS"""
    result = efris_manager.t104_get_aes_key()
    
    assert result is not None
    assert efris_manager.aes_key is not None
    assert len(efris_manager.aes_key) == 32  # 256-bit key
    print(f"✅ AES Key received: {efris_manager.aes_key.hex()[:16]}...")
```

---

### 3. Load Tests (`test_load.py`)

**Purpose**: Test system under concurrent load

**Characteristics**:
- 📊 Simulates multiple users
- ⏱️ Measures response times
- 🔥 Identifies bottlenecks
- 📈 Tests scalability

**Test Scenarios**:

| Scenario | Users | Duration | Purpose |
|----------|-------|----------|---------|
| Light | 10 | 1 min | Smoke test |
| Medium | 50 | 2 min | Normal operation |
| Heavy | 100 | 2 min | Peak load |
| Stress | 200+ | 5 min | Breaking point |

**Run Command**:
```bash
# Start Locust web UI
locust -f tests/test_load.py --host=http://localhost:8001

# Open browser to: http://localhost:8089

# Command-line mode (no UI)
locust -f tests/test_load.py --host=http://localhost:8001 \
       --users 100 --spawn-rate 10 --run-time 2m --headless
```

**Locust Web Interface**:

1. Open http://localhost:8089
2. Set number of users: `100`
3. Set spawn rate: `10` (users/second)
4. Click "Start swarming"
5. Monitor graphs and stats

**Performance Thresholds**:
```python
THRESHOLDS = {
    "fast": 200,        # < 200ms (excellent)
    "acceptable": 1000, # < 1s (good)
    "slow": 3000        # < 3s (poor)
}
```

---

## 🎯 Running Tests

### By Test Type

```bash
# Unit tests only (fast)
pytest tests/test_unit_core.py -v

# Integration tests only (requires credentials)
pytest tests/test_integration_efris.py -v -m integration

# Load tests
locust -f tests/test_load.py --host=http://localhost:8001
```

### By Marker

```bash
# Run only fast unit tests
pytest -v -m unit

# Run only integration tests
pytest -v -m integration

# Run slow tests
pytest -v -m slow

# Run everything EXCEPT slow tests
pytest -v -m "not slow"

# Run unit OR integration tests
pytest -v -m "unit or integration"
```

### With Coverage

```bash
# Generate coverage report
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# With branch coverage
pytest tests/ -v --cov=. --cov-report=html --cov-branch

# Fail if coverage < 70%
pytest tests/ -v --cov=. --cov-fail-under=70
```

### Specific Tests

```bash
# Run specific test file
pytest tests/test_unit_core.py -v

# Run specific test class
pytest tests/test_unit_core.py::TestSignatureGeneration -v

# Run specific test method
pytest tests/test_unit_core.py::TestSignatureGeneration::test_sign_creates_valid_signature -v

# Run tests matching pattern
pytest -v -k "signature"
pytest -v -k "test_sign or test_encrypt"
```

### Performance Benchmarks

```bash
# Run only benchmark tests
pytest tests/test_unit_core.py::TestPerformance -v --benchmark-only

# Compare benchmarks
pytest tests/test_unit_core.py::TestPerformance --benchmark-compare
```

---

## ✍️ Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Test suite for my feature"""
    
    @pytest.fixture
    def setup_data(self):
        """Fixture for test data"""
        return {"key": "value"}
    
    def test_basic_functionality(self, setup_data):
        """Test basic functionality"""
        # Arrange
        input_data = setup_data
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
@pytest.fixture
def efris_manager():
    """Create EfrisManager instance for testing"""
    manager = EfrisManager(
        tin="1000000000",
        device_no="1000000000_02",
        test_mode=True
    )
    return manager

def test_my_feature(efris_manager):
    """Test uses the fixture"""
    result = efris_manager.some_method()
    assert result is not None
```

### Mocking External APIs

```python
from unittest.mock import Mock, patch

@patch('requests.post')
def test_api_call(mock_post):
    """Test API call with mocked response"""
    # Setup mock
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"returnStateInfo": {"returnCode": "00"}}
    )
    
    # Call function that uses requests.post
    result = my_api_call()
    
    # Verify
    assert result["success"] == True
    mock_post.assert_called_once()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("invoice1", True),
    ("invoice2", True),
    ("invalid", False),
])
def test_validation(input, expected):
    """Test with multiple inputs"""
    result = validate_invoice(input)
    assert result == expected
```

### Testing Exceptions

```python
def test_raises_error():
    """Test that exception is raised"""
    with pytest.raises(ValueError, match="Invalid TIN"):
        process_tin("INVALID")
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_api_call()
    assert result is not None
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Location: `.github/workflows/tests.yml`

**Triggers**:
- ✅ Push to `main` or `develop` branches
- ✅ Pull requests
- ✅ Nightly scheduled runs (2 AM UTC)
- ✅ Manual workflow dispatch

**Jobs**:

#### 1. Unit Tests
- Runs on: `Python 3.9, 3.10, 3.11`
- Tests: Unit tests only
- Coverage: Uploaded to Codecov
- Artifacts: HTML coverage reports

#### 2. Integration Tests
- Runs on: Schedule or `[integration]` in commit message
- Tests: Real EFRIS API calls
- Requires: Secrets configured
- Timeout: 15 minutes

#### 3. Code Quality
- Black (formatter)
- isort (import sorting)
- Flake8 (linter)
- MyPy (type checker)
- Pylint (code analysis)

#### 4. Security Scan
- Safety (dependency vulnerabilities)
- Bandit (security linter)

#### 5. Performance Tests
- Runs on: Manual or `[performance]` in commit
- Benchmarks: Performance tests
- Artifacts: Benchmark JSON

### GitHub Secrets Required

```
EFRIS_TIN=your_test_tin
EFRIS_DEVICE_NO=your_device_number
EFRIS_CERT_PATH=path/to/certificate.p12
```

Add in: `Settings → Secrets and variables → Actions → New repository secret`

### Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/yourusername/EfrisAPI/workflows/Tests%20and%20Coverage/badge.svg)
[![codecov](https://codecov.io/gh/yourusername/EfrisAPI/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/EfrisAPI)
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Tests Skip Due to Missing Credentials

**Issue**: Integration tests skipped
```
tests/test_integration_efris.py::TestT104KeyExchangeIntegration::test_t104_key_exchange_success SKIPPED
```

**Solution**: Create `.env` file with credentials
```bash
echo "EFRIS_TIN=your_tin" >> .env
echo "EFRIS_DEVICE_NO=your_device" >> .env
echo "EFRIS_CERT_PATH=path/to/cert.p12" >> .env
```

#### 2. Import Errors

**Issue**: `ModuleNotFoundError: No module named 'pytest'`

**Solution**: Install dependencies
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock faker
```

#### 3. Certificate Not Found

**Issue**: `FileNotFoundError: Certificate file not found`

**Solution**: Check certificate path
```python
# In .env
EFRIS_CERT_PATH=D:/EfrisAPI/certificates/test_cert.p12
```

#### 4. Network Timeout

**Issue**: Integration tests timeout

**Solution**: Increase timeout in test
```python
@pytest.mark.timeout(30)  # 30 seconds
def test_slow_api_call():
    ...
```

#### 5. Coverage Too Low

**Issue**: `FAILED: coverage: total of 65% is less than fail-under=70%`

**Solution**: Write more tests or adjust threshold
```bash
# Adjust in pytest.ini
fail_under = 60
```

### Debug Mode

```bash
# Run with print statements shown
pytest tests/ -v -s

# Run with detailed traceback
pytest tests/ -v --tb=long

# Run with pdb debugger on failure
pytest tests/ -v --pdb

# Run last failed tests only
pytest tests/ -v --lf

# Run in verbose mode with timing
pytest tests/ -v --durations=10
```

---

## 📊 Performance Targets

### Response Time Targets

| Endpoint | Target | Acceptable | Poor |
|----------|--------|------------|------|
| Dashboard | < 100ms | < 500ms | > 1s |
| Invoice List | < 200ms | < 1s | > 2s |
| Invoice Submit | < 1s | < 3s | > 5s |
| Key Exchange (T104) | < 2s | < 5s | > 10s |

### Load Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Concurrent Users | 100+ | TBD |
| Requests/Second | 50+ | TBD |
| Failure Rate | < 1% | TBD |
| 95th Percentile Response | < 2s | TBD |

### Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| Overall | 70%+ | TBD |
| Core Functions | 90%+ | TBD |
| API Endpoints | 80%+ | TBD |
| Error Handlers | 100% | TBD |

---

## 📝 Test Commands Reference

### Quick Commands

```bash
# All unit tests (fast)
pytest tests/test_unit_core.py -v

# All integration tests (slow, needs credentials)
pytest tests/test_integration_efris.py -v -m integration

# Load test (web UI)
locust -f tests/test_load.py --host=http://localhost:8001

# Coverage report
pytest tests/ -v --cov=. --cov-report=html

# Specific test
pytest tests/test_unit_core.py::TestSignatureGeneration -v

# Pattern matching
pytest -v -k "signature"

# Exclude slow tests
pytest -v -m "not slow"

# Debug mode
pytest tests/ -v -s --tb=long

# Re-run failed tests
pytest tests/ -v --lf

# Show slowest tests
pytest tests/ -v --durations=10
```

---

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Best Practices
- Write tests before fixing bugs (TDD)
- Keep tests independent and isolated
- Use descriptive test names
- One assertion per test (when possible)
- Mock external dependencies
- Test edge cases and error conditions

### Test Naming Convention
```
test_<function_name>_<condition>_<expected_result>

Examples:
- test_sign_empty_string_raises_error
- test_encrypt_large_data_completes_within_one_second
- test_invoice_with_invalid_tin_validation_fails
```

---

## ✅ Checklist: Before Pushing Code

- [ ] All tests pass locally: `pytest tests/ -v`
- [ ] Coverage is above 70%: `pytest tests/ --cov=. --cov-report=term`
- [ ] Code formatted: `black .`
- [ ] Imports sorted: `isort .`
- [ ] No linting errors: `flake8 .`
- [ ] Type hints added: `mypy .`
- [ ] New tests written for new features
- [ ] Documentation updated

---

**Last Updated**: December 2024  
**Maintainer**: Development Team  
**Questions?**: Open an issue on GitHub

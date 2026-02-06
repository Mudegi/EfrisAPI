# 🧪 EFRIS Testing Quick Reference

One-page guide for running tests.

## 📦 Installation

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock faker locust
```

## ⚡ Quick Commands

### Run Tests

```bash
# All unit tests (fast)
pytest tests/test_unit_core.py -v

# All integration tests (needs credentials)
pytest tests/test_integration_efris.py -v -m integration

# All tests with coverage
pytest tests/ -v --cov=. --cov-report=html

# Specific test
pytest tests/test_unit_core.py::TestSignatureGeneration -v

# Pattern matching
pytest -v -k "signature"

# Exclude slow tests
pytest -v -m "not slow"
```

### Load Testing

```bash
# Start Locust (web UI at http://localhost:8089)
locust -f tests/test_load.py --host=http://localhost:8001

# Headless mode
locust -f tests/test_load.py --host=http://localhost:8001 \
       --users 100 --spawn-rate 10 --run-time 2m --headless
```

## 🔧 Setup for Integration Tests

Create `.env` file:

```env
EFRIS_TIN=your_test_tin
EFRIS_DEVICE_NO=your_device_number
EFRIS_CERT_PATH=path/to/certificate.p12
EFRIS_USE_TEST_MODE=true
```

## 📊 Test Markers

```bash
-m unit          # Unit tests only
-m integration   # Integration tests only
-m slow          # Slow tests only
-m "not slow"    # Exclude slow tests
```

## 📈 Coverage

```bash
# Generate HTML coverage report
pytest tests/ -v --cov=. --cov-report=html

# Open report (Windows)
start htmlcov/index.html

# Fail if coverage < 70%
pytest tests/ -v --cov=. --cov-fail-under=70
```

## 🎯 Test Types

| Type | File | Speed | Dependencies |
|------|------|-------|--------------|
| Unit | test_unit_core.py | ⚡ Fast | None |
| Integration | test_integration_efris.py | 🐢 Slow | EFRIS credentials |
| Load | test_load.py | 🔥 Variable | Locust |

## 🐛 Debug Mode

```bash
# Show print statements
pytest tests/ -v -s

# Debug on failure
pytest tests/ -v --pdb

# Detailed traceback
pytest tests/ -v --tb=long

# Re-run failed
pytest tests/ -v --lf
```

## 📋 Test Checklist

Before pushing code:

- [ ] `pytest tests/ -v` (all tests pass)
- [ ] `pytest tests/ --cov=.` (coverage > 70%)
- [ ] `black .` (code formatted)
- [ ] `flake8 .` (no lint errors)

## 🚀 CI/CD

### GitHub Actions

Automatically runs on:
- Push to `main` or `develop`
- Pull requests
- Nightly at 2 AM UTC
- Manual trigger

### Required Secrets

In GitHub Settings → Secrets:
```
EFRIS_TIN
EFRIS_DEVICE_NO
EFRIS_CERT_PATH
```

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_unit_core.py        # Unit tests (33 tests)
├── test_integration_efris.py # Integration tests (11 tests)
└── test_load.py             # Load tests
```

## 🔍 Common Issues

### Tests Skipped
**Problem**: Integration tests skipped  
**Solution**: Add `.env` with EFRIS credentials

### Import Error
**Problem**: `ModuleNotFoundError`  
**Solution**: `pip install pytest pytest-asyncio pytest-cov`

### Certificate Not Found
**Problem**: `FileNotFoundError`  
**Solution**: Check `EFRIS_CERT_PATH` in `.env`

### Timeout
**Problem**: Tests timeout  
**Solution**: Add `@pytest.mark.timeout(30)` decorator

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Unit test speed | < 1s each |
| Integration test success | > 95% |
| Code coverage | > 70% |
| Load (concurrent users) | 100+ |
| API response time | < 1s (95th percentile) |

## 📚 More Info

Full documentation: [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

**Quick Help**: `pytest --help` or visit https://docs.pytest.org/

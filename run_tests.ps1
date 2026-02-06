# EFRIS API Testing Script
# Convenient wrapper to run tests without PATH issues

$PYTHON = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "EFRIS API Test Runner" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check if Python exists
if (-not (Test-Path $PYTHON)) {
    Write-Host "Python not found at: $PYTHON" -ForegroundColor Red
    exit 1
}

# Parse command line arguments
$TestType = $args[0]

switch ($TestType) {
    "unit" {
        Write-Host "Running Unit Tests (fast)..." -ForegroundColor Green
        & $PYTHON -m pytest tests/test_unit_core.py -v
    }
    "integration" {
        Write-Host "Running Integration Tests (requires credentials)..." -ForegroundColor Yellow
        & $PYTHON -m pytest tests/test_integration_efris.py -v -m integration
    }
    "coverage" {
        Write-Host "Running Tests with Coverage..." -ForegroundColor Green
        & $PYTHON -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term
        Write-Host ""
        Write-Host "Coverage report generated in: htmlcov/index.html" -ForegroundColor Cyan
    }
    "quick" {
        Write-Host "Running Quick Tests (unit only)..." -ForegroundColor Green
        & $PYTHON -m pytest tests/test_unit_core.py -v
    }
    "load" {
        Write-Host "Starting Locust Load Testing..." -ForegroundColor Magenta
        Write-Host "Web UI available at: http://localhost:8089" -ForegroundColor Cyan
        & $PYTHON -m locust -f tests/test_load.py --host=http://localhost:8001
    }
    "all" {
        Write-Host "Running All Tests..." -ForegroundColor Green
        & $PYTHON -m pytest tests/ -v
    }
    default {
        Write-Host "EFRIS API Test Runner" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\run_tests.ps1 [command]" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  unit          - Run unit tests only" -ForegroundColor White
        Write-Host "  integration   - Run integration tests" -ForegroundColor White
        Write-Host "  coverage      - Run tests with coverage report" -ForegroundColor White
        Write-Host "  quick         - Run quick tests" -ForegroundColor White
        Write-Host "  load          - Start Locust load testing" -ForegroundColor White
        Write-Host "  all           - Run all tests" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Yellow
        Write-Host "  .\run_tests.ps1 unit" -ForegroundColor Gray
        Write-Host "  .\run_tests.ps1 coverage" -ForegroundColor Gray
        Write-Host "  .\run_tests.ps1 load" -ForegroundColor Gray
        Write-Host ""
    }
}

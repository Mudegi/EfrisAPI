@echo off
REM EFRIS API Testing - Quick Test Runner (Windows Batch)

set PYTHON=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe

echo ============================================================
echo 🧪 EFRIS API Test Runner
echo ============================================================
echo.

if "%1"=="" goto help
if "%1"=="unit" goto unit
if "%1"=="integration" goto integration
if "%1"=="coverage" goto coverage
if "%1"=="quick" goto quick
if "%1"=="load" goto load
if "%1"=="all" goto all
goto help

:unit
echo Running Unit Tests...
"%PYTHON%" -m pytest tests/test_unit_core.py -v
goto end

:integration
echo Running Integration Tests...
"%PYTHON%" -m pytest tests/test_integration_efris.py -v -m integration
goto end

:coverage
echo Running Tests with Coverage...
"%PYTHON%" -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term
echo.
echo Coverage report: htmlcov/index.html
goto end

:quick
echo Running Quick Tests...
"%PYTHON%" -m pytest tests/test_unit_core.py -v -m "not slow"
goto end

:load
echo Starting Locust Load Testing...
echo Web UI: http://localhost:8089
"%PYTHON%" -m locust -f tests/test_load.py --host=http://localhost:8001
goto end

:all
echo Running All Tests...
"%PYTHON%" -m pytest tests/ -v
goto end

:help
echo Usage: run_tests.bat [command]
echo.
echo Commands:
echo   unit          - Run unit tests only (fast)
echo   integration   - Run integration tests (requires credentials)
echo   coverage      - Run tests with coverage report
echo   quick         - Run quick tests (unit, no slow tests)
echo   load          - Start Locust load testing
echo   all           - Run all tests
echo.
echo Examples:
echo   run_tests.bat unit
echo   run_tests.bat coverage
echo   run_tests.bat load
goto end

:end

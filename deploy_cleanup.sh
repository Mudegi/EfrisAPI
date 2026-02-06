#!/bin/bash
# Post-Deployment Cleanup Script
# This runs after git pull to remove test files from production

echo "================================================"
echo "🧹 Cleaning up test files from production..."
echo "================================================"

# Remove test infrastructure
rm -rf tests/
rm -f run_tests.ps1 run_tests.bat pytest.ini
rm -f requirements-dev.txt

# Remove testing documentation
rm -f TESTING_GUIDE.md
rm -f TESTING_QUICKREF.md
rm -f TESTING_IMPLEMENTATION_COMPLETE.md

# Remove development scripts (optional - comment out if you need these)
# rm -f debug_*.py
# rm -f analyze_*.py
# rm -f check_*.py
# rm -f generate_*.py

# Remove CI/CD directory
rm -rf .github/

# Remove git-related files
rm -f .gitignore
rm -f .deployignore

echo "✅ Cleanup complete!"
echo ""
echo "📦 Production files:"
ls -lh *.py | head -10
echo ""
echo "📊 Disk usage:"
du -sh .

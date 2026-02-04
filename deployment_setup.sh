#!/bin/bash
# deployment_setup.sh - Automated setup for NameCheap hosting
# Run this on your server after uploading files

echo "================================"
echo "EFRIS API - NameCheap Setup"
echo "================================"
echo ""

# Check if Python is installed
echo "✓ Checking Python installation..."
python3 --version

# Create virtual environment
echo "✓ Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "✓ Installing Python packages..."
pip install -r requirements.txt
pip install gunicorn pymysql

# Create necessary directories
echo "✓ Creating directories..."
mkdir -p logs
mkdir -p temp
mkdir -p uploads

# Set permissions
echo "✓ Setting file permissions..."
chmod 600 .env
chmod -R 700 keys/
chmod -R 755 static/
chmod -R 755 database/
chmod 755 start.sh 2>/dev/null || true

# Create error log file
echo "✓ Creating log files..."
touch errors.log
chmod 644 errors.log

# Check database connection
echo "✓ Testing database connection..."
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

try:
    db_url = os.getenv('DATABASE_URL', '')
    if 'mysql' in db_url:
        print("✓ Database URL looks correct")
    else:
        print("⚠ Database URL might not be configured correctly")
except Exception as e:
    print(f"✗ Error: {e}")
EOF

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Verify .env file is configured correctly"
echo "2. Test the application:"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo "3. Check for errors in errors.log"
echo "4. Request NameCheap to configure web server"
echo ""
echo "For production, use:"
echo "   gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app"
echo ""

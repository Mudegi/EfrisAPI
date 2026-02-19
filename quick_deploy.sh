#!/bin/bash
# Quick deploy commands - Copy and paste these into your SSH terminal

echo "=== EFRIS API - Deploy Address Bug Fix ==="
echo ""
echo "Current directory:"
pwd
echo ""

echo "Step 1: Pulling latest code from GitHub..."
git pull origin main

echo ""
echo "Step 2: Reloading application..."
touch passenger_wsgi.py
mkdir -p tmp
touch tmp/restart.txt

echo ""
echo "✅ Deploy complete!"
echo ""
echo "Wait 30 seconds, then test your invoice submission."
echo ""
echo "Expected: HTTP 200 with FDN number"
echo "If still error: Run 'git log -1' to verify commit fdd87a0 is present"

@echo off
REM Quick deploy commands for Windows - Run this in PowerShell or CMD

echo === EFRIS API - Deploy Address Bug Fix ===
echo.

echo Current directory:
cd
echo.

echo Step 1: Pulling latest code from GitHub...
git pull origin main

echo.
echo Step 2: Reloading application...
type nul > passenger_wsgi.py
if not exist tmp mkdir tmp
type nul > tmp\restart.txt

echo.
echo ✅ Deploy complete!
echo.
echo Wait 30 seconds, then test your invoice submission.
echo.
echo Expected: HTTP 200 with FDN number
echo If still error: Run 'git log -1' to verify commit fdd87a0 is present

pause

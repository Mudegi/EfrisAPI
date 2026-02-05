# EFRIS Deployment Script
# This uploads only the files that have changed

# Configuration
$SERVER = "efrisintegration.nafacademy.com"
$USERNAME = "nafazplp"
$REMOTE_PATH = "/home/nafazplp/public_html/efrisintegration.nafacademy.com"

Write-Host "EFRIS Deployment to Production" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Files to upload:" -ForegroundColor Yellow
Write-Host "  - api_multitenant.py"
Write-Host "  - static/login.html"
Write-Host "  - static/landing.html"
Write-Host ""

$confirm = Read-Host "Type 'yes' to continue"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Upload these files via FTP/File Manager to:" -ForegroundColor Cyan
Write-Host "  $REMOTE_PATH" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then run on server:" -ForegroundColor Yellow
Write-Host "  touch $REMOTE_PATH/tmp/restart.txt" -ForegroundColor Yellow
Write-Host ""
Write-Host "Files ready in d:\EfrisAPI\" -ForegroundColor Green

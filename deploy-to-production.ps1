# EFRIS Auto-Deploy to Production
# Uploads all changed files to production server

param(
    [switch]$DryRun
)

$SERVER = "efrisintegration.nafacademy.com"
$USERNAME = "nafazplp"
$REMOTE_PATH = "/home/nafazplp/public_html/efrisintegration.nafacademy.com"
$LOCAL_PATH = "D:\EfrisAPI"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EFRIS Production Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Files to deploy (add more as needed)
$filesToDeploy = @(
    "api_multitenant.py",
    "passenger_wsgi.py",
    ".htaccess",
    "static/login.html",
    "static/landing.html",
    "static/dashboard.html",
    "static/reseller.html",
    "static/owner.html",
    "efris_client.py",
    "auth.py",
    "quickbooks_client.py"
)

Write-Host "Files to upload:" -ForegroundColor Yellow
foreach ($file in $filesToDeploy) {
    if (Test-Path "$LOCAL_PATH\$file") {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (not found - will skip)" -ForegroundColor Red
    }
}
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No files will be uploaded" -ForegroundColor Yellow
    Write-Host ""
    exit
}

$confirm = Read-Host "Deploy to PRODUCTION? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Checking for SSH/SCP availability..." -ForegroundColor Cyan

# Check if scp is available (comes with Git for Windows or OpenSSH)
$scpAvailable = Get-Command scp -ErrorAction SilentlyContinue

if ($scpAvailable) {
    Write-Host "✓ SCP found - Using SSH deployment" -ForegroundColor Green
    Write-Host ""
    
    foreach ($file in $filesToDeploy) {
        $localFile = "$LOCAL_PATH\$file"
        $remoteFile = "${USERNAME}@${SERVER}:${REMOTE_PATH}/$($file.Replace('\', '/'))"
        
        if (Test-Path $localFile) {
            Write-Host "Uploading: $file" -ForegroundColor Yellow
            scp $localFile $remoteFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Success" -ForegroundColor Green
            } else {
                Write-Host "  ✗ Failed" -ForegroundColor Red
            }
        }
    }
    
    Write-Host ""
    Write-Host "Restarting application..." -ForegroundColor Cyan
    ssh "${USERNAME}@${SERVER}" "touch ${REMOTE_PATH}/tmp/restart.txt"
    
    Write-Host ""
    Write-Host "✓ Deployment complete!" -ForegroundColor Green
    Write-Host "Testing health endpoint..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    try {
        $health = Invoke-RestMethod -Uri "https://${SERVER}/health" -Method Get
        Write-Host "✓ Server is healthy!" -ForegroundColor Green
        Write-Host "  Status: $($health.status)" -ForegroundColor White
        Write-Host "  Database: $($health.database)" -ForegroundColor White
    } catch {
        Write-Host "⚠ Could not reach health endpoint" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "✗ SCP not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install one of the following:" -ForegroundColor Yellow
    Write-Host "  1. Git for Windows (https://git-scm.com/download/win)" -ForegroundColor White
    Write-Host "  2. OpenSSH Client (Windows Settings > Apps > Optional Features)" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use manual upload via:" -ForegroundColor Yellow
    Write-Host "  - cPanel File Manager" -ForegroundColor White
    Write-Host "  - FileZilla FTP client" -ForegroundColor White
    Write-Host ""
    Write-Host "Files to upload are listed above." -ForegroundColor White
}

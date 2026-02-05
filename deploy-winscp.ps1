# Simple Deployment Script using WinSCP
# Install WinSCP from: https://winscp.net/eng/download.php

param(
    [string]$Password = ""
)

if ($Password -eq "") {
    $securePassword = Read-Host "Enter cPanel password" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

# WinSCP script
$scriptPath = "$env:TEMP\efris_deploy.txt"

$script = @"
option batch abort
option confirm off

# Connect to server
open sftp://nafazplp:$Password@efrisintegration.nafacademy.com

# Change to app directory
cd /home/nafazplp/public_html/efrisintegration.nafacademy.com

# Upload files (only if newer)
put -neweronly D:\EfrisAPI\api_multitenant.py
put -neweronly D:\EfrisAPI\passenger_wsgi.py
put -neweronly D:\EfrisAPI\.htaccess
put -neweronly D:\EfrisAPI\efris_client.py
put -neweronly D:\EfrisAPI\auth.py
put -neweronly D:\EfrisAPI\quickbooks_client.py

# Upload static files
put -neweronly D:\EfrisAPI\static\login.html static/
put -neweronly D:\EfrisAPI\static\landing.html static/
put -neweronly D:\EfrisAPI\static\dashboard.html static/
put -neweronly D:\EfrisAPI\static\reseller.html static/
put -neweronly D:\EfrisAPI\static\owner.html static/

# Restart app
call touch tmp/restart.txt

exit
"@

$script | Out-File -FilePath $scriptPath -Encoding ASCII

Write-Host "Deploying to production..." -ForegroundColor Cyan

# Run WinSCP
& "C:\Program Files (x86)\WinSCP\WinSCP.com" /script=$scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
    Write-Host "Waiting 3 seconds for app to restart..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    Write-Host "Testing site..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod "https://efrisintegration.nafacademy.com/health"
        Write-Host "✓ Site is live! Status: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Site may still be starting up" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "✗ Deployment failed" -ForegroundColor Red
}

# Cleanup
Remove-Item $scriptPath -ErrorAction SilentlyContinue

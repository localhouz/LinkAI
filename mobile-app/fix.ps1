#!/usr/bin/env pwsh
# Emergency fix script - tries multiple solutions

Write-Host "Attempting to fix the mobile app..." -ForegroundColor Cyan
Write-Host ""

# Clean up
Write-Host "Cleaning old files..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
}
if (Test-Path "package-lock.json") {
    Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
}

# Try install with legacy peer deps
Write-Host ""
Write-Host "Installing with --legacy-peer-deps..." -ForegroundColor Cyan
npm install --legacy-peer-deps --force

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Starting app..." -ForegroundColor Green
    Write-Host ""
    npx expo start -c
} else {
    Write-Host ""
    Write-Host "Install failed. Node 25 is incompatible." -ForegroundColor Red
    Write-Host ""
    Write-Host "You MUST downgrade to Node 20:" -ForegroundColor Yellow
    Write-Host "1. Download: https://nodejs.org/dist/v20.19.0/node-v20.19.0-x64.msi" -ForegroundColor Cyan
    Write-Host "2. Run the installer (it will replace Node 25)" -ForegroundColor Cyan
    Write-Host "3. Restart your terminal" -ForegroundColor Cyan
    Write-Host "4. Run this script again" -ForegroundColor Cyan
}

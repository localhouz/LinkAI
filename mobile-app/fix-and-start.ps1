#!/usr/bin/env pwsh
# Script to fix dependencies and start the Expo app

Write-Host "🔍 Checking Node version..." -ForegroundColor Cyan
$nodeVersion = node --version
Write-Host "Node version: $nodeVersion" -ForegroundColor Green

if ($nodeVersion -match "^v(18|20)\.") {
    Write-Host "✅ Node version is compatible!" -ForegroundColor Green
} else {
    Write-Host "⚠️  WARNING: Node $nodeVersion detected. This app requires Node 18 or 20 LTS." -ForegroundColor Yellow
    Write-Host "Please switch using: nvm use 18" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

Write-Host ""
Write-Host "🧹 Cleaning old dependencies..." -ForegroundColor Cyan

# Remove node_modules (safely)
if (Test-Path "node_modules") {
    Write-Host "Removing node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
}

# Remove package-lock.json
if (Test-Path "package-lock.json") {
    Write-Host "Removing package-lock.json..." -ForegroundColor Yellow
    Remove-Item -Force package-lock.json
}

Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ npm install failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Starting Expo with cache cleared..." -ForegroundColor Cyan
Write-Host ""

npx expo start -c

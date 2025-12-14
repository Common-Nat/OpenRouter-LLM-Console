# Frontend Test Installation Script
# Run this to install testing dependencies

Write-Host "Installing frontend testing dependencies..." -ForegroundColor Cyan

# Ensure Node.js is in PATH
$env:Path = "C:\Program Files\nodejs;" + $env:Path

# Navigate to frontend directory
Set-Location -Path $PSScriptRoot

# Clean install
Write-Host "`nCleaning node_modules..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Path "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "package-lock.json") {
    Remove-Item -Path "package-lock.json" -Force
}

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Dependencies installed successfully!" -ForegroundColor Green
    Write-Host "`nRun tests with:" -ForegroundColor Cyan
    Write-Host "  npm test              # Run once" -ForegroundColor White
    Write-Host "  npm run test:watch    # Watch mode" -ForegroundColor White
    Write-Host "  npm run test:ui       # Visual UI" -ForegroundColor White
    Write-Host "  npm run test:coverage # With coverage" -ForegroundColor White
} else {
    Write-Host "`n❌ Installation failed. See errors above." -ForegroundColor Red
    Write-Host "Try manually:" -ForegroundColor Yellow
    Write-Host "  cd frontend" -ForegroundColor White
    Write-Host "  npm install" -ForegroundColor White
}

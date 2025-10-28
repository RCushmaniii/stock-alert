# PowerShell script to build StockAlert MSI installer
# Usage: .\build_msi.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "StockAlert MSI Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not detected." -ForegroundColor Yellow
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        & .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "❌ Virtual environment not found. Please create it first:" -ForegroundColor Red
        Write-Host "   python -m venv venv" -ForegroundColor White
        exit 1
    }
}

Write-Host "✅ Virtual environment active" -ForegroundColor Green
Write-Host ""

# Step 2: Install build dependencies
Write-Host "📦 Installing build dependencies..." -ForegroundColor Cyan
pip install -r requirements-build.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 3: Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Cyan
if (Test-Path ".\build") {
    Remove-Item -Recurse -Force ".\build"
}
if (Test-Path ".\dist") {
    Remove-Item -Recurse -Force ".\dist"
}
Write-Host "✅ Build directories cleaned" -ForegroundColor Green
Write-Host ""

# Step 4: Build MSI
Write-Host "🔨 Building MSI installer..." -ForegroundColor Cyan
python setup.py bdist_msi
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ MSI build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ MSI build complete" -ForegroundColor Green
Write-Host ""

# Step 5: Display results
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MSI installer location:" -ForegroundColor Yellow
Get-ChildItem -Path ".\dist" -Filter "*.msi" | ForEach-Object {
    Write-Host "  📦 $($_.FullName)" -ForegroundColor White
    Write-Host "     Size: $([math]::Round($_.Length / 1MB, 2)) MB" -ForegroundColor Gray
}
Write-Host ""
Write-Host "You can now distribute the MSI file to install StockAlert on Windows systems." -ForegroundColor Cyan

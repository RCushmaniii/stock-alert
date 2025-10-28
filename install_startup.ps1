# PowerShell script to add StockAlert to Windows Startup
# This makes StockAlert run automatically when Windows starts

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "StockAlert Startup Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the startup folder path
$startupFolder = [Environment]::GetFolderPath("Startup")

# Try to find StockAlert in common installation locations
$possiblePaths = @(
    "$env:LOCALAPPDATA\Programs\StockAlert\StockAlert.exe",
    "C:\Program Files\StockAlert\StockAlert.exe",
    "C:\Program Files (x86)\StockAlert\StockAlert.exe"
)

$stockAlertPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $stockAlertPath = $path
        break
    }
}

if (-not $stockAlertPath) {
    Write-Host "❌ StockAlert not found in common installation locations" -ForegroundColor Red
    Write-Host "Please install StockAlert first." -ForegroundColor Yellow
    exit 1
}

$shortcutPath = Join-Path $startupFolder "StockAlert.lnk"
$workingDir = Split-Path $stockAlertPath -Parent

# Create shortcut
Write-Host "Creating startup shortcut..." -ForegroundColor Cyan
Write-Host "Found StockAlert at: $stockAlertPath" -ForegroundColor Green
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $stockAlertPath
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.Description = "StockAlert - Market Hours Monitor"
$Shortcut.Save()

Write-Host "✅ Startup shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "StockAlert will now start automatically when you log in to Windows." -ForegroundColor Cyan
Write-Host "It will run in the background and only monitor during market hours." -ForegroundColor Cyan
Write-Host ""
Write-Host "To remove from startup, delete:" -ForegroundColor Yellow
Write-Host "  $shortcutPath" -ForegroundColor White

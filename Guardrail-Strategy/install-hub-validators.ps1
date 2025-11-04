# Install Guardrails Hub Validators
# This script handles Windows encoding issues with emoji characters

Write-Host "Installing Guardrails Hub validators..." -ForegroundColor Cyan
Write-Host ""

# Set UTF-8 encoding for proper emoji display
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup.bat first to create the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Activate venv
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "ERROR: Could not find activation script!" -ForegroundColor Red
    exit 1
}

# Install detect_pii validator
Write-Host "Installing hub://guardrails/detect_pii..." -ForegroundColor Yellow
$detectPiiResult = & venv\Scripts\guardrails.exe hub install hub://guardrails/detect_pii 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ detect_pii installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install detect_pii" -ForegroundColor Red
    Write-Host $detectPiiResult
}

Write-Host ""

# Install toxic_language validator
Write-Host "Installing hub://guardrails/toxic_language..." -ForegroundColor Yellow
$toxicResult = & venv\Scripts\guardrails.exe hub install hub://guardrails/toxic_language 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ toxic_language installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install toxic_language" -ForegroundColor Red
    Write-Host $toxicResult
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Hub validators installation complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


# PowerShell wrapper script for seed_mock_conversations.py
# Usage: .\seed_mock_conversations.ps1

$scriptPath = Join-Path $PSScriptRoot "seed_mock_conversations.py"

# Try to find Python
$pythonCmd = $null

# Try common Python commands on Windows
$pythonCommands = @("py", "python3", "python")

foreach ($cmd in $pythonCommands) {
    try {
        $null = Get-Command $cmd -ErrorAction Stop
        $pythonCmd = $cmd
        break
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python or use Docker:" -ForegroundColor Red
    Write-Host "   docker compose exec ofh-dashboard-backend python scripts/seed_mock_conversations.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "Running mock conversation seeder..." -ForegroundColor Cyan
Write-Host "Using Python: $pythonCmd" -ForegroundColor Gray

# Change to backend directory if not already there
$backendDir = Split-Path (Split-Path $PSScriptRoot)
if ((Get-Location).Path -ne $backendDir) {
    Push-Location $backendDir
    try {
        & $pythonCmd $scriptPath
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
} else {
    & $pythonCmd $scriptPath
    $exitCode = $LASTEXITCODE
}

if ($exitCode -ne 0) {
    Write-Host "❌ Script failed with exit code $exitCode" -ForegroundColor Red
    exit $exitCode
}


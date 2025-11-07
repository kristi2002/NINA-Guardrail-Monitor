# PowerShell script to remove the problematic __consumer_offsets-42 partition
# This will allow Kafka to recreate it and start successfully

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$PROBLEM_PARTITION = "__consumer_offsets-42"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Removing Problematic Partition" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will delete the $PROBLEM_PARTITION partition." -ForegroundColor Yellow
Write-Host "Kafka will recreate it automatically when it starts." -ForegroundColor White
Write-Host "Consumer offsets for this partition will be reset." -ForegroundColor Yellow
Write-Host ""

# Step 1: Make sure Kafka and ZooKeeper are stopped
Write-Host "Step 1: Verifying Kafka and ZooKeeper are stopped..." -ForegroundColor Yellow
$runningProcesses = Get-Process -Name "java" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmd -like "*kafka*" -or $cmd -like "*zookeeper*") {
            return $_
        }
    } catch {
        # Ignore
    }
}

if ($runningProcesses) {
    Write-Host "WARNING - Kafka/ZooKeeper processes are still running!" -ForegroundColor Red
    Write-Host "Please stop them before removing partitions." -ForegroundColor Yellow
    $runningProcesses | ForEach-Object {
        Write-Host "  Process ID: $($_.Id)" -ForegroundColor Gray
    }
    exit 1
} else {
    Write-Host "OK - No Kafka/ZooKeeper processes running" -ForegroundColor Green
}
Write-Host ""

# Step 2: Remove the problematic partition
Write-Host "Step 2: Removing $PROBLEM_PARTITION partition..." -ForegroundColor Yellow
$partitionPath = Join-Path $KAFKA_LOG_DIR $PROBLEM_PARTITION

if (Test-Path $partitionPath) {
    Write-Host "  Found partition directory: $PROBLEM_PARTITION" -ForegroundColor Cyan
    
    # Get size before deletion
    $size = (Get-ChildItem -Path $partitionPath -Recurse -File -ErrorAction SilentlyContinue | 
        Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "  Partition size: $sizeMB MB" -ForegroundColor Gray
    
    try {
        # Remove read-only attributes first
        Get-ChildItem -Path $partitionPath -Recurse -Force -ErrorAction SilentlyContinue | 
            ForEach-Object { $_.IsReadOnly = $false }
        
        # Delete the partition directory
        Remove-Item -Path $partitionPath -Recurse -Force -ErrorAction Stop
        Write-Host "  OK - Partition removed successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "Success - Partition Removed" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Start ZooKeeper" -ForegroundColor White
        Write-Host "2. Start Kafka (it will recreate the partition)" -ForegroundColor White
        Write-Host "3. Create the guardrail_control topic:" -ForegroundColor White
        Write-Host "   python scripts\create_guardrail_control_topic.py" -ForegroundColor Gray
        Write-Host ""
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "  ERROR - Could not remove partition: $errorMsg" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Trying alternative method..." -ForegroundColor Yellow
        
        # Try using takeown and attrib
        try {
            Write-Host "  Taking ownership..." -ForegroundColor Cyan
            & takeown /F $partitionPath /R /D Y 2>&1 | Out-Null
            Start-Sleep -Seconds 1
            
            Write-Host "  Removing read-only attributes..." -ForegroundColor Cyan
            & attrib -R "$partitionPath\*.*" /S /D 2>&1 | Out-Null
            Start-Sleep -Seconds 1
            
            Write-Host "  Deleting..." -ForegroundColor Cyan
            Remove-Item -Path $partitionPath -Recurse -Force -ErrorAction Stop
            Write-Host "  OK - Partition removed using alternative method" -ForegroundColor Green
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Cyan
            Write-Host "Success - Partition Removed" -ForegroundColor Green
            Write-Host "============================================================" -ForegroundColor Cyan
        } catch {
            Write-Host "  ERROR - Still cannot remove partition" -ForegroundColor Red
            Write-Host "  You may need to:" -ForegroundColor Yellow
            Write-Host "    1. Run this script as Administrator" -ForegroundColor Gray
            Write-Host "    2. Manually delete: $partitionPath" -ForegroundColor Gray
            Write-Host "    3. Or use Windows Explorer to delete the folder" -ForegroundColor Gray
            exit 1
        }
    }
} else {
    Write-Host "  Partition directory not found (may have been removed already)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Partition Already Removed" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now start Kafka and it should work." -ForegroundColor White
    Write-Host ""
}
Write-Host ""


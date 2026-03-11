# Setup daily paper fetch as a Windows scheduled task
# Run this script once from an elevated PowerShell prompt

$PythonPath = (Get-Command python).Source
$ProjectDir = "c:\Users\Admin\Documents\projects\cryptollm"
$ScriptPath = "$ProjectDir\survey\scripts\daily_pipeline.py"

# Create the scheduled task to run daily at 9:00 AM
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument $ScriptPath `
    -WorkingDirectory $ProjectDir

$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName "CryptoLLM_DailyPaper" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Fetch new ePrint papers and push notification to iPhone"

Write-Host ""
Write-Host "Scheduled task 'CryptoLLM_DailyPaper' created." -ForegroundColor Green
Write-Host "It will run daily at 9:00 AM."
Write-Host ""
Write-Host "To test: schtasks /run /tn CryptoLLM_DailyPaper"
Write-Host "To remove: schtasks /delete /tn CryptoLLM_DailyPaper /f"

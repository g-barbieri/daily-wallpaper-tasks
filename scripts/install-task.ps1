param(
  [string]$TaskName = "Daily Wallpaper Tasks",
  [string]$Time = "08:00"
)

Set-Location -LiteralPath $PSScriptRoot\..

$timeSpan = [TimeSpan]::ParseExact($Time, "hh\:mm", $null)
$startDate = [DateTime]::Today.Add($timeSpan)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSScriptRoot\run-wallpaper.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At $startDate
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

Write-Host "Scheduled task '$TaskName' registered for $Time daily."

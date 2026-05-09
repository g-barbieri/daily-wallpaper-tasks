Set-Location -LiteralPath $PSScriptRoot\..

$desktop = [Environment]::GetFolderPath('Desktop')
$target = Join-Path $PSScriptRoot 'run-wallpaper.ps1'
$shortcutPath = Join-Path $desktop 'Update Today Wallpaper.lnk'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$target`""
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,167"
$shortcut.Save()

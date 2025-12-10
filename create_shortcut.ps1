# PowerShell script to create desktop shortcut for ACT UI

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\ACT UI Builder.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\launch_ui.bat"
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.Description = "Launch ACT UI Builder for development and testing"
$Shortcut.IconLocation = "python.exe,0"
$Shortcut.Save()

Write-Host "Shortcut created on Desktop: ACT UI Builder.lnk" -ForegroundColor Green
Write-Host "Double-click it to launch the UI!" -ForegroundColor Green


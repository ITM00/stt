param(
    [string]$ShortcutName = "STT Desktop",
    [string]$IconPath = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath ($ShortcutName + ".lnk")
$launcherPath = Join-Path $scriptDir "start-stt.ps1"

if (-not (Test-Path $launcherPath)) {
    Write-Error "Launcher script not found: $launcherPath"
}

if ([string]::IsNullOrWhiteSpace($IconPath)) {
    $defaultIcon = Join-Path $scriptDir "stt.ico"
    if (Test-Path $defaultIcon) {
        $IconPath = $defaultIcon
    } else {
        $IconPath = Join-Path $PSHOME "powershell.exe"
    }
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = $IconPath
$shortcut.Description = "Start STT Desktop"
$shortcut.Save()

Write-Host "Created shortcut: $shortcutPath"
Write-Host "Target: powershell.exe $($shortcut.Arguments)"
Write-Host "Icon: $IconPath"


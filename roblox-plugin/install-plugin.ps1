$ErrorActionPreference = "Stop"

$src = Join-Path $PSScriptRoot "VibeCoderInstaller.rbxmx"
if (-not (Test-Path $src)) {
  throw "Missing plugin file: $src"
}

$destDir = Join-Path $env:LOCALAPPDATA "Roblox\Plugins"
if (-not (Test-Path $destDir)) {
  New-Item -ItemType Directory -Path $destDir | Out-Null
}

$dest = Join-Path $destDir "VibeCoderInstaller.rbxmx"
Copy-Item -Force $src $dest

Write-Host "Installed: $dest"
Write-Host "Restart Roblox Studio, then enable it in Plugins -> Manage Plugins."


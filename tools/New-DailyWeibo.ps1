$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dailyDir = Join-Path $root "daily"
if (-not (Test-Path $dailyDir)) {
    New-Item -ItemType Directory -Path $dailyDir | Out-Null
}

$date = Get-Date -Format "yyyy-MM-dd"
$target = Join-Path $dailyDir "$($date)-10-weibo-drafts.md"

if (Test-Path $target) {
    Write-Host "Daily draft already exists: $target"
    exit 0
}

$template = Get-ChildItem -Path $root -Filter "03_*.md" | Select-Object -First 1
if ($null -eq $template) {
    throw "Cannot find daily draft template: 03_*.md"
}

Copy-Item -Path $template -Destination $target
Write-Host "Created daily draft: $target"

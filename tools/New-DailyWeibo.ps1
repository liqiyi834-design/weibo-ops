$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dailyDir = Join-Path $root "daily"
if (-not (Test-Path $dailyDir)) {
    New-Item -ItemType Directory -Path $dailyDir | Out-Null
}

function Get-BeijingDateName {
    $utcNow = [DateTimeOffset]::UtcNow
    $bj = $utcNow.ToOffset([TimeSpan]::FromHours(8))
    return $bj.ToString("yyyy-MM-dd")
}

$dateName = Get-BeijingDateName
$target = Join-Path $dailyDir "$($dateName)-10-weibo-drafts.md"

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

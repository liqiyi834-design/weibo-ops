$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $root "output"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$dateName = Get-Date -Format "yyyy-MM-dd"
$target = Join-Path $outputDir "post_skeletons_$dateName.md"

$historyPath = Join-Path $root "data\news_history.csv"
if (Test-Path $historyPath) {
    $topics = Import-Csv -Path $historyPath -Encoding UTF8 |
        Select-Object -ExpandProperty title -Unique |
        Select-Object -First 10
} else {
    $topics = @("topic 1", "topic 2", "topic 3")
}

$lines = @()
$lines += "# Post Skeletons $dateName"
$lines += ""
$lines += "Use these as draft starters. Verify facts before publishing."
$lines += ""

foreach ($topic in $topics) {
    $lines += "## $topic"
    $lines += ""
    $lines += "Opening judgment:"
    $lines += ""
    $lines += "Known facts:"
    $lines += "- "
    $lines += "- "
    $lines += ""
    $lines += "Human translation:"
    $lines += ""
    $lines += "Sharp but fair take:"
    $lines += ""
    $lines += "Comment hook:"
    $lines += "Question for comments:"
    $lines += ""
    $lines += "---"
    $lines += ""
}

$lines | Set-Content -Path $target -Encoding UTF8
Write-Host "Created post skeletons: $target"

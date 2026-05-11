$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$samplePath = Join-Path $root "data\weibo_post_samples.csv"
$outputDir = Join-Path $root "output"

if (-not (Test-Path $samplePath)) {
    throw "Missing sample file: $samplePath"
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

function To-Number {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 0
    }

    $text = $Value.Trim()
    $numText = ($text -replace "[^0-9\.]", "")
    if ([string]::IsNullOrWhiteSpace($numText)) {
        return 0
    }

    $num = [double]$numText
    $wan = [string]([char]0x4e07)
    if ($text -like "*$wan*") {
        return [int]($num * 10000)
    }

    return [int]$num
}

$rows = Import-Csv -Path $samplePath -Encoding UTF8 | ForEach-Object {
    $reposts = To-Number $_.reposts
    $comments = To-Number $_.comments
    $likes = To-Number $_.likes
    $score = ($likes * 1) + ($comments * 3) + ($reposts * 5)

    $_.interaction_score = $score
    $_
}

$dateName = Get-Date -Format "yyyy-MM-dd"
$rankPath = Join-Path $outputDir "weibo_sample_rank_$dateName.csv"
$reportPath = Join-Path $outputDir "weibo_sample_report_$dateName.md"

$ranked = $rows | Sort-Object @{ Expression = { [int]$_.interaction_score }; Descending = $true }
$ranked | Export-Csv -Path $rankPath -NoTypeInformation -Encoding UTF8

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Weibo Sample Report $dateName")
$lines.Add("")
$lines.Add("Ranking formula: likes * 1 + comments * 3 + reposts * 5")
$lines.Add("")
$lines.Add("## Top Samples")
$lines.Add("")

$top = @($ranked | Select-Object -First 20)
foreach ($item in $top) {
    $lines.Add("### " + $item.account + " / score " + $item.interaction_score)
    $lines.Add("")
    $lines.Add("- field: " + $item.field)
    $lines.Add("- publish_time: " + $item.publish_time)
    $lines.Add("- context_event: " + $item.context_event)
    $lines.Add("- event_stage: " + $item.event_stage)
    $lines.Add("- related_hotwords: " + $item.related_hotwords)
    $lines.Add("- timing_advantage: " + $item.timing_advantage)
    $lines.Add("- why_now: " + $item.why_now)
    $lines.Add("- reposts/comments/likes: " + $item.reposts + " / " + $item.comments + " / " + $item.likes)
    $lines.Add("- content_type: " + $item.content_type)
    $lines.Add("- learnable_point: " + $item.learnable_point)
    $lines.Add("")
    $body = $item.body
    if ($body.Length -gt 500) {
        $body = $body.Substring(0, 500) + "..."
    }
    $lines.Add($body)
    $lines.Add("")
}

$lines | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Created rank: $rankPath"
Write-Host "Created report: $reportPath"

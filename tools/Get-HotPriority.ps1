$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataPath = Join-Path $root "data\news_history.csv"
$outputDir = Join-Path $root "output"

if (-not (Test-Path $dataPath)) {
    throw "Cannot find data file: $dataPath"
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

function Parse-HotValue {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 0
    }

    $text = $Value.Trim()
    $numberText = ($text -replace "[^0-9\.]", "")
    if ([string]::IsNullOrWhiteSpace($numberText)) {
        return 0
    }

    $number = [double]$numberText
    $wan = [string]([char]0x4e07)
    if ($text -like "*$wan*") {
        return [int]($number * 10000)
    }

    return [int]$number
}

function Get-HeatScore {
    param([int]$HotValue)

    if ($HotValue -le 0) {
        return 0
    }

    $score = [math]::Log10($HotValue + 1) * 10
    return [math]::Round([math]::Min($score, 70), 2)
}

function Get-RiskPenalty {
    param([string]$Risk)

    switch ($Risk) {
        "high" { return 25 }
        "medium" { return 10 }
        "low" { return 0 }
        default { return 5 }
    }
}

function Get-Level {
    param([double]$Score)

    if ($Score -ge 80) { return "S" }
    if ($Score -ge 60) { return "A" }
    if ($Score -ge 40) { return "B" }
    if ($Score -ge 20) { return "C" }
    return "D"
}

function Parse-RankValue {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 0
    }

    $numberText = ($Value.Trim() -replace "[^0-9]", "")
    if ([string]::IsNullOrWhiteSpace($numberText)) {
        return 0
    }

    return [int]$numberText
}

function Test-ContainsAny {
    param(
        [string]$Text,
        [string[]]$Needles
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    foreach ($needle in $Needles) {
        if ($Text -like "*$needle*") {
            return $true
        }
    }

    return $false
}

function Get-DualChartBonus {
    param($Item)

    $chartText = "$($Item.charts);$($Item.source);$($Item.category)"
    $hasHotChart = Test-ContainsAny $chartText @("热搜", "微博热搜", "hot", "weibo_hot")
    $hasEntertainmentChart = Test-ContainsAny $chartText @("文娱", "娱乐", "entertainment", "weibo_entertainment")

    if (-not ($hasHotChart -and $hasEntertainmentChart)) {
        return 0
    }

    $hotRank = Parse-RankValue $Item.hot_rank
    $entertainmentRank = Parse-RankValue $Item.entertainment_rank

    if ($hotRank -gt 0 -and $hotRank -le 10 -and $entertainmentRank -gt 0 -and $entertainmentRank -le 10) {
        return 25
    }

    if (
        ($hotRank -gt 0 -and $hotRank -le 10 -and $entertainmentRank -gt 0 -and $entertainmentRank -le 30) -or
        ($entertainmentRank -gt 0 -and $entertainmentRank -le 10 -and $hotRank -gt 0 -and $hotRank -le 30)
    ) {
        return 18
    }

    return 12
}

$today = Get-Date
$windows = @(
    @{ Name = "d1"; Days = 1; Weight = 35; Cap = 4 },
    @{ Name = "d3"; Days = 3; Weight = 25; Cap = 5 },
    @{ Name = "d7"; Days = 7; Weight = 18; Cap = 6 },
    @{ Name = "d15"; Days = 15; Weight = 14; Cap = 7 },
    @{ Name = "d30"; Days = 30; Weight = 10; Cap = 8 },
    @{ Name = "d90"; Days = 90; Weight = 7; Cap = 10 },
    @{ Name = "d180"; Days = 180; Weight = 5; Cap = 12 },
    @{ Name = "d365"; Days = 365; Weight = 3; Cap = 15 }
)

$rows = Import-Csv -Path $dataPath -Encoding UTF8 | ForEach-Object {
    $eventKey = $_.event_key
    if ([string]::IsNullOrWhiteSpace($eventKey)) {
        $eventKey = $_.title
    }

    [pscustomobject]@{
        date = [datetime]$_.date
        title = $_.title
        category = $_.category
        event_key = $eventKey
        tags = $_.tags
        hot = $_.hot
        hot_value = Parse-HotValue $_.hot
        source = $_.source
        charts = $_.charts
        hot_rank = $_.hot_rank
        entertainment_rank = $_.entertainment_rank
        risk = $_.risk
        status = $_.status
    }
}

$results = foreach ($group in ($rows | Group-Object event_key)) {
    $items = @($group.Group)
    $latest = $items |
        Sort-Object @{ Expression = "date"; Descending = $true }, @{ Expression = "hot_value"; Descending = $true } |
        Select-Object -First 1
    $maxHot = ($items | Measure-Object hot_value -Maximum).Maximum

    $recurrenceScore = 0
    $windowCounts = @{}

    foreach ($window in $windows) {
        $since = $today.AddDays(-1 * [int]$window.Days)
        $count = @($items | Where-Object { $_.date -ge $since }).Count
        $windowCounts[$window.Name] = $count

        if ($count -gt 1) {
            $effectiveCount = [math]::Min($count - 1, [int]$window.Cap)
            $recurrenceScore += $effectiveCount * [double]$window.Weight
        }
    }

    $recurrenceScore = [math]::Min($recurrenceScore, 80)

    $daysSinceLatest = [math]::Max(0, ($today.Date - $latest.date.Date).Days)
    $freshScore = [math]::Max(0, 20 - ($daysSinceLatest * 2))
    $heatScore = Get-HeatScore $maxHot
    $publicValueScore = if ($latest.category -in @("social", "health", "finance", "tech", "international", "education", "policy")) { 12 } else { 6 }
    $dualChartBonus = ($items | ForEach-Object { Get-DualChartBonus $_ } | Measure-Object -Maximum).Maximum
    if ($null -eq $dualChartBonus) {
        $dualChartBonus = 0
    }
    $riskPenalty = Get-RiskPenalty $latest.risk

    $priorityScore = [math]::Round($heatScore + $recurrenceScore + $freshScore + $publicValueScore + $dualChartBonus - $riskPenalty, 2)

    [pscustomobject]@{
        level = Get-Level $priorityScore
        priority_score = $priorityScore
        event_key = $group.Name
        latest_title = $latest.title
        category = $latest.category
        max_hot = $maxHot
        dual_chart_bonus = $dualChartBonus
        count_1d = $windowCounts["d1"]
        count_3d = $windowCounts["d3"]
        count_7d = $windowCounts["d7"]
        count_15d = $windowCounts["d15"]
        count_30d = $windowCounts["d30"]
        count_90d = $windowCounts["d90"]
        count_180d = $windowCounts["d180"]
        count_365d = $windowCounts["d365"]
        risk = $latest.risk
        suggested_action = if ($priorityScore -ge 80) { "must_publish_today" } elseif ($priorityScore -ge 60) { "publish_today" } elseif ($priorityScore -ge 40) { "draft_backup" } else { "watch" }
        tags = $latest.tags
    }
}

$dateName = Get-Date -Format "yyyy-MM-dd"
$outputPath = Join-Path $outputDir "hot_priority_$dateName.csv"
$results |
    Sort-Object @{ Expression = "priority_score"; Descending = $true }, @{ Expression = "max_hot"; Descending = $true } |
    Export-Csv -Path $outputPath -NoTypeInformation -Encoding UTF8

Write-Host "Created priority report: $outputPath"

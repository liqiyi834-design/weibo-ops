param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("hot", "entertainment")]
    [string]$Chart,

    [Parameter(Mandatory = $true)]
    [string]$InputJson,

    [Parameter(Mandatory = $false)]
    [string]$DateName,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $root "output"
}
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

function Get-BeijingDateName {
    $utcNow = [DateTimeOffset]::UtcNow
    $bj = $utcNow.ToOffset([TimeSpan]::FromHours(8))
    return $bj.ToString("yyyy-MM-dd")
}

if ([string]::IsNullOrWhiteSpace($DateName)) {
    $DateName = Get-BeijingDateName
}

if (-not (Test-Path $InputJson)) {
    throw "Missing input JSON: $InputJson"
}

function Get-JsonSafe {
    param([string]$Path)
    try {
        return (Get-Content -Raw -Encoding UTF8 -Path $Path) | ConvertFrom-Json
    } catch {
        # Fallback: try default encoding
        return (Get-Content -Raw -Path $Path) | ConvertFrom-Json
    }
}

function Find-ListStartIndex {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return 0
    }

    # Avoid embedding non-ASCII anchors (Windows PowerShell may load scripts as ANSI).
    # We rely primarily on the regex hot-number guard instead.
    return 0
}

function Parse-HotlistItems {
    param([string]$Text)

    $clean = ($Text -replace "\s+", " ").Trim()
    if ([string]::IsNullOrWhiteSpace($clean)) {
        return @()
    }

    $start = Find-ListStartIndex $clean
    if ($start -gt 0) {
        $clean = $clean.Substring($start)
    }

    # Core pattern:
    # rank (1-50) + term (non-greedy) + optional flag + hot number + stop before next rank.
    # Important: hot numbers are typically >= 5 digits; this prevents menu digits from being mis-read.
    # NOTE: Keep this script ASCII-only for Windows PowerShell encoding quirks.
    $flagChars = @([char]0x65B0, [char]0x70ED, [char]0x7206, [char]0x6CB8) # new/hot/explosive/boil flags
    $flagPattern = "(?:" + (($flagChars | ForEach-Object { [regex]::Escape($_) }) -join "|") + ")"
    # PowerShell does not treat backslash as an escape in strings, so use single backslashes for regex tokens.
    $pattern = "(?<!\d)(?<rank>[1-9]\d?)\s+(?<term>.+?)\s+(?<flag>$flagPattern)?\s*(?<hot>\d{5,})\s*(?=(?:[1-9]\d?)\s+|$)"

    $matches = [regex]::Matches($clean, $pattern)
    $items = @()

    foreach ($m in $matches) {
        $rank = [int]$m.Groups["rank"].Value
        if ($rank -lt 1 -or $rank -gt 50) { continue }

        $term = $m.Groups["term"].Value.Trim()
        $term = ($term -replace "\s+", " ").Trim()

        $flag = $m.Groups["flag"].Value.Trim()
        $hot = $m.Groups["hot"].Value.Trim()

        # Guardrail: drop the leading nav chunk some captures include (e.g., "1 推荐 ... 社会 5 <real term>").
        if ($term -match "(^|\s)[1-9]\d?\s+$") { continue }
        if ($term -match "(^|\s)[1-9]\d?\s+[\p{IsCJKUnifiedIdeographs}#@]" ) {
            # If another rank number appears inside term, keep only the substring after the last such rank token.
            $rankInside = [regex]::Matches($term, "(?<!\d)([1-9]\d?)\s+")
            if ($rankInside.Count -gt 0) {
                $last = $rankInside[$rankInside.Count - 1]
                $cut = $last.Index + $last.Length
                if ($cut -gt 0 -and $cut -lt $term.Length) {
                    $term = $term.Substring($cut).Trim()
                }
            }
        }

        $items += [pscustomobject]@{
            rank = $rank
            term = $term
            flag = $flag
            hot  = $hot
        }
    }

    # Deduplicate by rank; keep first.
    $dedup = @{}
    $final = @()
    foreach ($it in ($items | Sort-Object rank)) {
        if (-not $dedup.ContainsKey($it.rank)) {
            $dedup[$it.rank] = $true
            $final += $it
        }
    }
    return $final
}

$json = Get-JsonSafe $InputJson
$visible = [string]$json.visible_text
$url = [string]$json.page_url
$title = [string]$json.page_title
$capturedAt = [string]$json.captured_at

$items = Parse-HotlistItems $visible
if ($items.Count -eq 0) {
    throw "Parsed 0 items from visible_text. Please recapture the list page with more items visible."
}

$chartName = if ($Chart -eq "hot") { "weibo_hotlist" } else { "weibo_entertainment" }
$outPath = Join-Path $OutputDir ("{0}_{1}.csv" -f $chartName, $DateName)

$items | Export-Csv -Path $outPath -NoTypeInformation -Encoding UTF8

Write-Host "Chart: $Chart"
Write-Host "Input: $InputJson"
Write-Host "Captured: $capturedAt"
Write-Host "Page: $title / $url"
Write-Host "Items: $($items.Count)"
Write-Host "Wrote: $outPath"

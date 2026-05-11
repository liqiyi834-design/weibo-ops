$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$inbox = Join-Path $root "samples\inbox"
$processed = Join-Path $root "samples\processed"
$csvPath = Join-Path $root "data\weibo_samples.csv"

if (-not (Test-Path $inbox)) {
    New-Item -ItemType Directory -Path $inbox | Out-Null
}

if (-not (Test-Path $processed)) {
    New-Item -ItemType Directory -Path $processed | Out-Null
}

if (-not (Test-Path $csvPath)) {
    "captured_at,page_title,page_url,sample_index,possible_author,hashtags,metrics,body_text,links,notes" |
        Set-Content -Path $csvPath -Encoding UTF8
}

$files = Get-ChildItem -Path $inbox -Filter "*.json" -File
if ($files.Count -eq 0) {
    Write-Host "No JSON files found in $inbox"
    exit 0
}

$rows = foreach ($file in $files) {
    $json = Get-Content -Path $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($null -ne $json.samples) {
        foreach ($sample in $json.samples) {
            [pscustomobject]@{
                captured_at = $sample.captured_at
                page_title = $sample.page_title
                page_url = $sample.page_url
                sample_index = $sample.index
                possible_author = $sample.possible_author
                hashtags = (($sample.hashtags | ForEach-Object { $_ }) -join ";")
                metrics = $sample.metrics
                body_text = $sample.body_text
                links = (($sample.links | ForEach-Object { $_ }) -join ";")
                notes = ""
            }
        }
    } elseif ($null -ne $json.visible_text) {
        [pscustomobject]@{
            captured_at = $json.captured_at
            page_title = $json.page_title
            page_url = $json.page_url
            sample_index = 1
            possible_author = ""
            hashtags = (($json.visible_text | Select-String -Pattern "#[^#\s]{1,40}#" -AllMatches).Matches.Value -join ";")
            metrics = ""
            body_text = $json.visible_text
            links = (($json.links | ForEach-Object { $_ }) -join ";")
            notes = "simple_visible_capture"
        }
    }
}

$rowList = @($rows)
$rowList | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8 -Append

foreach ($file in $files) {
    $target = Join-Path $processed $file.Name
    if (Test-Path $target) {
        $target = Join-Path $processed ("{0}_{1}" -f ([guid]::NewGuid().ToString("N")), $file.Name)
    }
    try {
        Move-Item -LiteralPath $file.FullName -Destination $target -ErrorAction Stop
    } catch {
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "Copied sample to processed; original may still be locked: $($file.Name)"
    }
}

Write-Host "Imported $($rowList.Count) samples into $csvPath"

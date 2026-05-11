$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $root "data"
$csvPath = Join-Path $dataDir "telegram_inbox.csv"
$statePath = Join-Path $dataDir "telegram_inbox_offset.txt"

if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

if (-not (Test-Path $csvPath)) {
    "update_id,date,chat_id,chat_type,username,first_name,text,has_photo,caption" |
        Set-Content -Path $csvPath -Encoding UTF8
}

$token = $env:TELEGRAM_BOT_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    $token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "User")
}
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Missing TELEGRAM_BOT_TOKEN."
}

$offset = ""
if (Test-Path $statePath) {
    $saved = (Get-Content -Path $statePath -Raw).Trim()
    if (-not [string]::IsNullOrWhiteSpace($saved)) {
        $offset = "&offset=$saved"
    }
}

$uri = "https://api.telegram.org/bot$token/getUpdates?timeout=1$offset"
$updates = Invoke-RestMethod -Uri $uri -Method Get
if (-not $updates.ok) {
    throw "Telegram getUpdates failed."
}

$rows = foreach ($update in $updates.result) {
    $message = $update.message
    if ($null -eq $message) {
        $message = $update.channel_post
    }
    if ($null -ne $message) {
        [pscustomobject]@{
            update_id = $update.update_id
            date = ([DateTimeOffset]::FromUnixTimeSeconds([int64]$message.date).LocalDateTime.ToString("yyyy-MM-dd HH:mm:ss"))
            chat_id = $message.chat.id
            chat_type = $message.chat.type
            username = $message.chat.username
            first_name = $message.chat.first_name
            text = $message.text
            has_photo = ($null -ne $message.photo)
            caption = $message.caption
        }
    }
}

$rowList = @($rows)
if ($rowList.Count -gt 0) {
    $rowList | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8 -Append
    $nextOffset = ([int64]($rowList | Select-Object -Last 1).update_id) + 1
    Set-Content -Path $statePath -Value $nextOffset -Encoding ASCII
}

Write-Host "Imported $($rowList.Count) Telegram update(s) into $csvPath"

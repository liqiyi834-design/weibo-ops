param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot does not exist: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

$checks = @()

$python = Get-Command python -ErrorAction SilentlyContinue
$checks += [pscustomobject]@{
    Name = "python"
    Ok = [bool]$python
    Detail = if ($python) { (& python --version) } else { "not found" }
}

$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermes) {
    $localHermes = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\hermes.exe"
    if (Test-Path -LiteralPath $localHermes) {
        $hermes = [pscustomobject]@{ Source = $localHermes }
    }
}
$checks += [pscustomobject]@{
    Name = "hermes"
    Ok = [bool]$hermes
    Detail = if ($hermes) { $hermes.Source } else { "not found; install Hermes CLI first" }
}

$mcpImport = $false
$mcpDetail = ""
try {
    $mcpDetail = (& python -c "import mcp_server.server; print('mcp import ok')" 2>&1)
    $mcpImport = $LASTEXITCODE -eq 0
} catch {
    $mcpDetail = $_.Exception.Message
}

$checks += [pscustomobject]@{
    Name = "mcp_server"
    Ok = $mcpImport
    Detail = $mcpDetail
}

$checks | Format-Table -AutoSize

if ($checks.Ok -contains $false) {
    exit 1
}

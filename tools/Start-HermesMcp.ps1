param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot does not exist: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath "mcp_server\server.py")) {
    throw "mcp_server\server.py not found. ProjectRoot may be incorrect: $ProjectRoot"
}

$env:FASTMCP_LOG_LEVEL = "ERROR"

& $Python -m mcp_server.server

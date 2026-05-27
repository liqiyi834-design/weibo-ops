param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Python = "python",
    [string]$OutputPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "configs\hermes.mcp.local.yaml"),
    [switch]$PrintOnly
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot does not exist: $ProjectRoot"
}

$resolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$startScript = Join-Path $resolvedProjectRoot "tools\Start-HermesMcp.ps1"

if (-not (Test-Path -LiteralPath $startScript)) {
    throw "Start-HermesMcp.ps1 not found: $startScript"
}

$pythonCommand = Get-Command $Python -ErrorAction Stop
$pythonPath = $pythonCommand.Source

$yamlProjectRoot = $resolvedProjectRoot.Replace("\", "\\")
$yamlStartScript = $startScript.Replace("\", "\\")
$yamlPythonPath = $pythonPath.Replace("\", "\\")

$content = @"
# Generated from this clone. Do not commit this file.
# Copy the `mcp_servers.hotcomment_ai` block into ~/.hermes/config.yaml.
# Keep API keys, cookies, and account tokens in .env or environment variables.

mcp_servers:
  hotcomment_ai:
    command: "powershell"
    args:
      - "-NoProfile"
      - "-ExecutionPolicy"
      - "Bypass"
      - "-File"
      - "$yamlStartScript"
      - "-ProjectRoot"
      - "$yamlProjectRoot"
      - "-Python"
      - "$yamlPythonPath"
    tools:
      include:
        - get_hot_topics
        - select_comment_topics
        - classify_topic
        - research_topic_sources
        - rerank_topics_with_research
        - retrieve_knowledge
        - extract_style_memory
        - ingest_style_memory
        - ingest_knowledge
        - ingest_current_research
        - build_generation_context
        - generate_comment
        - save_draft
        - list_drafts
        - record_draft_feedback
        - summarize_draft_feedback
        - safety_check
        - send_review_message
"@

if ($PrintOnly) {
    Write-Output $content
    exit 0
}

$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

Set-Content -LiteralPath $OutputPath -Value $content -Encoding utf8
Write-Output "Wrote Hermes MCP config snippet: $OutputPath"

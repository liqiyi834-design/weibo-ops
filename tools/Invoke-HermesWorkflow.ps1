param(
    [ValidateSet("daily_hot_topics_review", "draft_generation_queue", "safety_review_digest", "auto_candidate_to_review_text", "ingest_current_research_to_rag", "style_memory_ingest", "draft_feedback_review", "summarize_draft_feedback")]
    [string]$Workflow,
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ExtraPrompt = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot does not exist: $ProjectRoot"
}

$workflowPath = Join-Path $ProjectRoot "configs\hermes.workflows\$Workflow.md"
if (-not (Test-Path -LiteralPath $workflowPath)) {
    throw "Workflow prompt not found: $workflowPath"
}

$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermes) {
    $localHermes = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\hermes.exe"
    if (Test-Path -LiteralPath $localHermes) {
        $hermes = [pscustomobject]@{ Source = $localHermes }
    }
}
if (-not $hermes) {
    throw "Hermes CLI not found. Install Hermes first, then run tools\Test-HermesProjectPrereqs.ps1."
}

$hermesHome = [Environment]::GetEnvironmentVariable("HERMES_HOME", "User")
if (-not $hermesHome) {
    $hermesHome = Join-Path $env:LOCALAPPDATA "hermes"
}
$env:HERMES_HOME = $hermesHome

$prompt = Get-Content -LiteralPath $workflowPath -Raw -Encoding utf8
if ($ExtraPrompt.Trim()) {
    $prompt = $prompt.TrimEnd() + "`n`n## User Extra Input`n`n" + $ExtraPrompt
}

if ($DryRun) {
    Write-Output $prompt
    exit 0
}

Set-Location -LiteralPath $ProjectRoot
& $hermes.Source -z $prompt --accept-hooks

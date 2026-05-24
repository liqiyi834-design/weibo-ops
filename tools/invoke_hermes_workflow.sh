#!/usr/bin/env bash
set -euo pipefail

WORKFLOW=""
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTRA_PROMPT=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow)
      WORKFLOW="$2"
      shift 2
      ;;
    --project-root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --extra-prompt)
      EXTRA_PROMPT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$WORKFLOW" in
  daily_hot_topics_review|draft_generation_queue|safety_review_digest|auto_candidate_to_review_text|ingest_current_research_to_rag|style_memory_ingest)
    ;;
  "")
    echo "--workflow is required" >&2
    exit 2
    ;;
  *)
    echo "Unknown workflow: $WORKFLOW" >&2
    exit 2
    ;;
esac

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
WORKFLOW_PATH="$PROJECT_ROOT/configs/hermes.workflows/$WORKFLOW.md"

if [[ ! -f "$WORKFLOW_PATH" ]]; then
  echo "Workflow prompt not found: $WORKFLOW_PATH" >&2
  exit 1
fi

PROMPT="$(cat "$WORKFLOW_PATH")"
if [[ -n "${EXTRA_PROMPT// }" ]]; then
  PROMPT="$PROMPT

## User Extra Input

$EXTRA_PROMPT"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi

cd "$PROJECT_ROOT"
exec hermes -z "$PROMPT" --accept-hooks

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUTPUT_PATH=""
PRINT_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --print-only)
      PRINT_ONLY=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
START_SCRIPT="$PROJECT_ROOT/tools/start_hermes_mcp.sh"
PYTHON_PATH="$(command -v "$PYTHON_BIN")"

if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$PROJECT_ROOT/configs/hermes.mcp.local.yaml"
fi

if [[ ! -x "$START_SCRIPT" ]]; then
  chmod +x "$START_SCRIPT"
fi

CONTENT="$(cat <<EOF
# Generated from this clone. Do not commit this file.
# Copy the mcp_servers.hotcomment_ai block into ~/.hermes/config.yaml.
# Keep API keys, cookies, and account tokens in .env or environment variables.

mcp_servers:
  hotcomment_ai:
    command: "$START_SCRIPT"
    args:
      - "--project-root"
      - "$PROJECT_ROOT"
      - "--python"
      - "$PYTHON_PATH"
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
EOF
)"

if [[ "$PRINT_ONLY" -eq 1 ]]; then
  printf '%s\n' "$CONTENT"
else
  mkdir -p "$(dirname "$OUTPUT_PATH")"
  printf '%s\n' "$CONTENT" > "$OUTPUT_PATH"
  echo "Wrote Hermes MCP config snippet: $OUTPUT_PATH"
fi

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

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
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

cd "$PROJECT_ROOT"

if [[ ! -f "mcp_server/server.py" ]]; then
  echo "mcp_server/server.py not found. ProjectRoot may be incorrect: $PROJECT_ROOT" >&2
  exit 1
fi

export FASTMCP_LOG_LEVEL=ERROR
exec "$PYTHON_BIN" -m mcp_server.server

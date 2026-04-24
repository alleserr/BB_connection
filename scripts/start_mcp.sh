#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Virtual environment not found at ${PROJECT_ROOT}/.venv"
  exit 1
fi

exec .venv/bin/python -m app.main serve-mcp --host 127.0.0.1 --port 8000

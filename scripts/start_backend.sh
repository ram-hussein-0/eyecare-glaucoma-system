#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTORCH_ENABLE_MPS_FALLBACK=1

if [ -x "$PWD/.venv/bin/python" ]; then
  PYTHON="$PWD/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

exec "$PYTHON" -m uvicorn \
  backend.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000 \
  --reload-exclude '_backup_*' \
  --reload-exclude 'phase_*'

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PYTHONPATH="$PWD:${PYTHONPATH:-}"

if [ -x "$PWD/.venv/bin/python" ]; then
  PYTHON="$PWD/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

exec "$PYTHON" -m streamlit run frontend/Home.py

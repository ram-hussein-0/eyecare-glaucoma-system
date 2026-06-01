#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python3 -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --reload-exclude '_backup_*' --reload-exclude 'phase_*'

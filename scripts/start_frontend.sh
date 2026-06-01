#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python3 -m streamlit run frontend/Home.py

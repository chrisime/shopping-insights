#!/bin/sh
set -eu

exec "$(dirname "$0")/venv/bin/python" -m uvicorn api.main:app --reload --port 8000

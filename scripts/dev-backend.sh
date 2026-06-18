#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"
exec uvicorn app.main:app --reload --host "${AV_TOKENVAULT_HOST:-127.0.0.1}" --port "${AV_TOKENVAULT_PORT:-8000}"

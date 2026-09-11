#!/usr/bin/env bash
set -euo pipefail

export AV_TOKENVAULT_DEFAULT_TRANSCRIBER="${AV_TOKENVAULT_DEFAULT_TRANSCRIBER:-faster-whisper-base}"
export AV_TOKENVAULT_DEFAULT_TEXT_ENCODER="${AV_TOKENVAULT_DEFAULT_TEXT_ENCODER:-sentence-transformers:BAAI/bge-small-zh-v1.5}"

exec "$(dirname "$0")/dev-backend.sh"

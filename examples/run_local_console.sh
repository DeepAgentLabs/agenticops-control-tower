#!/usr/bin/env bash
# Install agenticops-control-tower[api] first. See docs/authentication.md.
# Export persistent deployment tokens before running. This script intentionally
# does not generate new tokens on restart or print existing credentials.
set -euo pipefail
: "${AGENTICOPS_READ_TOKEN:?Generate and export your reader token first; see docs/authentication.md}"
: "${AGENTICOPS_WRITE_TOKEN:?Generate and export a separate writer token first; see docs/authentication.md}"
exec agenticops-control-tower serve \
    --host 127.0.0.1 \
    --port "${AGENTICOPS_PORT:-8000}" \
    --database "${AGENTICOPS_DATABASE:-registry.sqlite}"

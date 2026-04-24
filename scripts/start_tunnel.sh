#!/usr/bin/env bash

set -euo pipefail

if command -v cloudflared >/dev/null 2>&1; then
  exec cloudflared tunnel --url http://127.0.0.1:8000
fi

if command -v docker >/dev/null 2>&1; then
  exec docker run --rm cloudflare/cloudflared:latest tunnel --url http://host.docker.internal:8000
fi

echo "Neither cloudflared nor docker is available"
exit 1

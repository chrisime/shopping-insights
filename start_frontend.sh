#!/bin/sh
set -eu

cd "$(dirname "$0")/web"
if command -v corepack >/dev/null 2>&1; then
  exec corepack pnpm dev
elif command -v pnpm >/dev/null 2>&1; then
  exec pnpm dev
else
  echo "Error: neither corepack nor pnpm found. Install Node.js + corepack or pnpm." >&2
  exit 1
fi

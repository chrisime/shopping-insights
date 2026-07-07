#!/bin/sh
set -u

cd "$(dirname "$0")/web"
pnpm dev 2>/dev/null && exit 0
corepack pnpm dev 2>/dev/null && exit 0
npx pnpm dev 2>/dev/null && exit 0

echo "Error: pnpm not found. Install it via: npm install -g pnpm" >&2
exit 1

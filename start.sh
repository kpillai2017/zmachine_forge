#!/usr/bin/env bash
# Compile the example game and play it in the terminal (curses if possible).
set -euo pipefail
cd "$(dirname "$0")"
python -m zforge compile examples/cloak.zil -o build/cloak.z5 --emit-asm
exec python -m zforge run build/cloak.z5 "$@"

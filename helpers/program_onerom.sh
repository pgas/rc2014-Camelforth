#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROM="${1:-$ROOT/build/Mini_II_camelforth.bin}"
shift $(( $# > 0 ? 1 : 0 ))

if [[ ! -f "$ROM" ]]; then
  echo "ROM image not found: $ROM" >&2
  exit 1
fi

exec onerom program \
  --plugin system/usb \
  --slot "file=$ROM,type=SST39SF010" \
  "$@"

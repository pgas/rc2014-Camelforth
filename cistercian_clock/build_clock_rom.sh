#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

"$ROOT/helpers/cross_compile.py" \
  "$ROOT/RTC/RTC.f" \
  "$ROOT/matrix8x8/matrix8x8.f" \
  "$ROOT/cistercian_clock/cistercian_clock.f" \
  --out-bin "$ROOT/build/camelforth_clock_ram.bin" \
  --out-hex "$ROOT/build/camelforth_clock_ram.hex"

"$ROOT/helpers/build_rom.py" \
  "$ROOT/RTC/RTC.f" \
  "$ROOT/matrix8x8/matrix8x8.f" \
  "$ROOT/cistercian_clock/cistercian_clock.f" \
  --start-word "CIST-CLOCK" \
  "$@"

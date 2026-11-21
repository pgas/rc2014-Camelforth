#!/usr/bin/env python3
"""
spool.py - Strips comments and spools Forth source over serial to CamelForth on RC2014.
Works alongside an open minicom session (writes TX only; minicom displays RX).
Supports spooling one or multiple files sequentially in a single session.
"""

import sys
import time
import os
import argparse
from pathlib import Path

from strip_comments import strip_forth_comments

DEFAULT_PORT = "/dev/tty.usbmodem08481"
DEFAULT_DELAY = 0.08  # 80 ms line pacing for safe Z80 dictionary compilation

def resolve_file(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_file():
        candidate = Path(__file__).resolve().parent.parent / file_path
        if candidate.is_file():
            return candidate
        print(f"Error: file '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    return path

def spool_files(file_paths: list[str], port: str = DEFAULT_PORT, line_delay: float = DEFAULT_DELAY):
    # Validate and prepare all files before touching the serial port
    prepared = []
    total_lines = 0
    for fp in file_paths:
        path = resolve_file(fp)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw_source = f.read()
        cleaned = strip_forth_comments(raw_source, keep_blank_lines=False)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        prepared.append((path, lines))
        total_lines += len(lines)

    if not prepared:
        print("No files to spool.")
        return

    print(f"Opening {port} (write-only)...")
    try:
        fd = os.open(port, os.O_WRONLY | os.O_NOCTTY)
    except Exception as e:
        print(f"Failed to open {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Spooling {len(prepared)} file(s) ({total_lines} total lines) with {int(line_delay * 1000)}ms pacing...")
    print("Watch your minicom screen for CamelForth output!\n")

    try:
        for f_idx, (path, lines) in enumerate(prepared, 1):
            print(f"[{f_idx}/{len(prepared)}] Spooling {len(lines)} lines from '{path}'...")
            for idx, line in enumerate(lines, 1):
                payload = (line + "\r").encode("ascii", errors="replace")
                os.write(fd, payload)
                time.sleep(line_delay)
                if idx % 20 == 0 or idx == len(lines):
                    print(f"  Line {idx}/{len(lines)} sent...")
            if f_idx < len(prepared):
                time.sleep(line_delay * 2)  # Brief pause between files
    finally:
        os.close(fd)

    print(f"\nDone! Spooled {total_lines} lines across {len(prepared)} file(s) to {port}.")

def main():
    parser = argparse.ArgumentParser(
        description="Minify and spool one or more Forth source files over serial to CamelForth."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Forth source file(s) to spool in sequence (default: RTC/RTC.f)"
    )
    parser.add_argument("-p", "--port", default=DEFAULT_PORT, help=f"Serial port (default: {DEFAULT_PORT})")
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_DELAY, help=f"Line delay in seconds (default: {DEFAULT_DELAY})")
    args = parser.parse_args()

    files = args.files if args.files else ["RTC/RTC.f"]
    spool_files(files, port=args.port, line_delay=args.delay)

if __name__ == "__main__":
    main()

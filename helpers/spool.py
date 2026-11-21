#!/usr/bin/env python3
"""
spool.py - Strips comments and spools Forth source over serial to CamelForth on RC2014.
Works alongside an open minicom session (writes TX only; minicom displays RX).
"""

import sys
import time
import os
import argparse
from pathlib import Path

from strip_comments import strip_forth_comments

DEFAULT_PORT = "/dev/tty.usbmodem08481"
DEFAULT_DELAY = 0.06  # 60 ms line pacing for Z80 dictionary compilation

def spool(file_path: str, port: str = DEFAULT_PORT, line_delay: float = DEFAULT_DELAY):
    path = Path(file_path)
    if not path.is_file():
        print(f"Error: file '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw_source = f.read()

    # Automatically minify Forth comments and blank lines before spooling
    cleaned = strip_forth_comments(raw_source, keep_blank_lines=False)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    print(f"Opening {port} (write-only)...")
    try:
        fd = os.open(port, os.O_WRONLY | os.O_NOCTTY)
    except Exception as e:
        print(f"Failed to open {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Spooling {len(lines)} minified lines from '{file_path}' with {int(line_delay * 1000)}ms pacing...")
    print("Watch your minicom screen for CamelForth output!\n")

    try:
        for idx, line in enumerate(lines, 1):
            payload = (line + "\r").encode("ascii", errors="replace")
            os.write(fd, payload)
            time.sleep(line_delay)
            if idx % 10 == 0 or idx == len(lines):
                print(f"Spooling: {idx}/{len(lines)} lines sent...")
    finally:
        os.close(fd)

    print(f"\nDone! Spooled {len(lines)} lines to {port}.")

def main():
    parser = argparse.ArgumentParser(description="Minify and spool Forth source over serial to CamelForth.")
    parser.add_argument("file", nargs="?", default="RTC/RTC.f", help="Forth source file to spool (default: RTC/RTC.f)")
    parser.add_argument("-p", "--port", default=DEFAULT_PORT, help=f"Serial port (default: {DEFAULT_PORT})")
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_DELAY, help=f"Line delay in seconds (default: {DEFAULT_DELAY})")
    args = parser.parse_args()

    spool(args.file, port=args.port, line_delay=args.delay)

if __name__ == "__main__":
    main()

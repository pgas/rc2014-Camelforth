#!/usr/bin/env python3
"""
cistercian_clock.py - Visualizes Cistercian numerals on an 8x8 LED matrix.

Usage:
  ./helpers/cistercian_clock.py [HH MM]
  ./helpers/cistercian_clock.py [HH:MM]
  ./helpers/cistercian_clock.py          (uses current local time)

Options:
  --dow 0..6    Weekday override (0=Mon, 1=Tue, ..., 6=Sun)
  --dst 0|1     Daylight Saving Time override (0=off, 1=on)
"""

import sys
import argparse
import datetime

# Digit bitmaps (3 rows: outer, middle, inner)
# Right wing (Cols 4-6, Bits 3, 2, 1)
CIST_RIGHT = [
    [0x00, 0x00, 0x00],  # 0
    [0x0E, 0x00, 0x00],  # 1 (outer bar)
    [0x00, 0x00, 0x0E],  # 2 (inner bar)
    [0x08, 0x04, 0x02],  # 3 (diagonal \)
    [0x02, 0x04, 0x08],  # 4 (diagonal /)
    [0x0E, 0x02, 0x08],  # 5 (1 + 4)
    [0x02, 0x02, 0x02],  # 6 (outer vertical)
    [0x0E, 0x02, 0x02],  # 7 (1 + 6)
    [0x02, 0x02, 0x0E],  # 8 (2 + 6)
    [0x0E, 0x02, 0x0E],  # 9 (1 + 2 + 6)
]

# Left wing (Cols 0-2, Bits 7, 6, 5), horizontal mirror
CIST_LEFT = [
    [0x00, 0x00, 0x00],  # 0
    [0xE0, 0x00, 0x00],  # 1
    [0x00, 0x00, 0xE0],  # 2
    [0x20, 0x40, 0x80],  # 3
    [0x80, 0x40, 0x20],  # 4
    [0xE0, 0x80, 0x20],  # 5
    [0x80, 0x80, 0x80],  # 6
    [0xE0, 0x80, 0x80],  # 7
    [0x80, 0x80, 0xE0],  # 8
    [0xE0, 0x80, 0xE0],  # 9
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def render_matrix(hh: int, mm: int, dow: int, dst: int):
    """
    Renders 8x8 matrix display buffer (8 bytes).
    Bit 4 (0x10) is stem; Bit 0 (0x01) is status.
    """
    buf = [0x10] * 8  # Center stem on all 8 rows

    # Status column (Col 7 / Bit 0)
    if 0 <= dow < 7:
        buf[dow] |= 0x01
    if dst:
        buf[7] |= 0x01

    h1, h0 = divmod(hh, 10)
    m1, m0 = divmod(mm, 10)

    # Top wings: minute tens (left) & minute units (right)
    for i in range(3):
        buf[i] |= CIST_LEFT[m1][i] | CIST_RIGHT[m0][i]

    # Bottom wings: hour tens (left) & hour units (right), vertically mirrored
    for i in range(3):
        buf[5 + i] |= CIST_LEFT[h1][2 - i] | CIST_RIGHT[h0][2 - i]

    return buf, (h1, h0, m1, m0)

def print_clock(hh: int, mm: int, dow: int, dst: int):
    buf, (h1, h0, m1, m0) = render_matrix(hh, mm, dow, dst)
    dow_name = WEEKDAYS[dow] if 0 <= dow < 7 else f"Day {dow}"
    dst_str = "ON" if dst else "OFF"

    print(f"Cistercian Clock: {hh:02d}:{mm:02d} ({dow_name}, DST: {dst_str})")
    print("-" * 52)
    print(f"  Top-Left     (Min Tens):  {m1}  |  Top-Right    (Min Units):  {m0}")
    print(f"  Bottom-Left  (Hour Tens): {h1}  |  Bottom-Right (Hour Units): {h0}")
    print()
    print("       Col: 0 1 2   3   4 5 6   7 (Status)")

    row_labels = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "DST Active" if dst else "DST Inactive"
    ]

    for r, byte_val in enumerate(buf):
        row_chars = []
        for c in range(8):
            bit = (byte_val >> (7 - c)) & 1
            row_chars.append("#" if bit else ".")
            if c in (2, 3, 6):
                row_chars.append("|")
        indicator = "<- " + row_labels[r]
        print(f"    Row {r}:  {' '.join(row_chars)}  {indicator}")

    print()
    hex_str = " ".join(f"{b:02X}" for b in buf)
    print(f"Matrix Buffer (HEX): {hex_str}")
    print(f"Forth Test Command:  {hh} {mm} {dow} {dst} CIST-SET .CIST")

def parse_time_arg(args):
    now = datetime.datetime.now()
    default_hh = now.hour
    default_mm = now.minute
    default_dow = now.weekday()  # 0=Monday .. 6=Sunday
    default_dst = 1 if (now.astimezone().dst() and now.astimezone().dst().total_seconds() > 0) else 0

    if not args.time:
        return default_hh, default_mm, default_dow, default_dst

    if len(args.time) == 1:
        part = args.time[0]
        if ":" in part:
            pieces = part.split(":")
            hh, mm = int(pieces[0]), int(pieces[1])
        else:
            hh = int(part)
            mm = 0
    elif len(args.time) >= 2:
        hh = int(args.time[0])
        mm = int(args.time[1])
    else:
        hh, mm = default_hh, default_mm

    return hh, mm, default_dow, default_dst

def main():
    parser = argparse.ArgumentParser(
        description="Render Cistercian 8x8 clock for given or current time."
    )
    parser.add_argument(
        "time",
        nargs="*",
        help="Time as 'HH MM' or 'HH:MM' (defaults to current system time)"
    )
    parser.add_argument(
        "--dow",
        type=int,
        choices=range(7),
        help="Day of week: 0=Mon .. 6=Sun (default: current day)"
    )
    parser.add_argument(
        "--dst",
        type=int,
        choices=[0, 1],
        help="Daylight Saving Time: 0=off, 1=on (default: current system DST)"
    )

    args = parser.parse_args()

    hh, mm, default_dow, default_dst = parse_time_arg(args)
    dow = args.dow if args.dow is not None else default_dow
    dst = args.dst if args.dst is not None else default_dst

    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        print(f"Error: Invalid time {hh:02d}:{mm:02d}. Hour must be 0-23, minute 0-59.", file=sys.stderr)
        sys.exit(1)

    print_clock(hh, mm, dow, dst)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_rom.py - Builds a 16KB CamelForth ROM with RTC, matrix8x8, and cistercian_clock
preloaded in ROM and auto-started on boot, plus a 128KB RC2014 Mini II image.
"""

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))
from strip_comments import strip_forth_comments

MINI2_DIR = ROOT.parent / "mini2"
DEFAULT_FACTORY_HEX = MINI2_DIR / "ROMs" / "Factory" / "Mini II v1.2.HEX"
DEFAULT_FILES = [
    ROOT / "RTC" / "RTC.f",
    ROOT / "matrix8x8" / "matrix8x8.f",
    ROOT / "cistercian_clock" / "cistercian_clock.f",
]

TOTAL_SIZE = 131072
BANK_SIZE = 16384
HOOK_ADDR = 0x1A92      # Free space in 8K CamelForth ROM after CRT init table
COLD_ABORT_XT = 0x18D4  # Offset in COLD where DW ABORT (0x1375) resides
SRC_ADDR = 0x2000       # Upper 8K of the 16K bank


def parse_intel_hex(hex_path):
    data = bytearray([0xFF] * TOTAL_SIZE)
    base = 0
    with open(hex_path, "r", encoding="latin1") as f:
        for line in f:
            line = line.strip()
            if not line.startswith(":"):
                continue
            bc = int(line[1:3], 16)
            addr = int(line[3:7], 16)
            rtype = int(line[7:9], 16)
            if rtype == 0:
                for i in range(bc):
                    val = int(line[9 + i * 2:11 + i * 2], 16)
                    target = base + addr + i
                    if target < TOTAL_SIZE:
                        data[target] = val
            elif rtype == 4:
                base = int(line[9:13], 16) << 16
            elif rtype == 1:
                break
    return data


def write_intel_hex(data, hex_path):
    with open(hex_path, "w", encoding="latin1") as f:
        curr_segment = -1
        for addr in range(0, len(data), 16):
            seg = addr >> 16
            if seg != curr_segment:
                curr_segment = seg
                cksum = (-(2 + 4 + (curr_segment >> 8) + (curr_segment & 0xFF))) & 0xFF
                f.write(f":02000004{curr_segment:04X}{cksum:02X}\n")

            chunk = data[addr:addr + 16]
            offset = addr & 0xFFFF
            cksum = (-(16 + (offset >> 8) + (offset & 0xFF) + sum(chunk))) & 0xFF
            hex_bytes = "".join(f"{b:02X}" for b in chunk)
            f.write(f":10{offset:04X}00{hex_bytes}{cksum:02X}\n")
        f.write(":00000001FF\n")


def insert_bank(base_data, payload, bank):
    if not (0 <= bank <= 7):
        raise ValueError(f"Bank must be between 0 and 7, got {bank}")
    if len(payload) > BANK_SIZE:
        raise ValueError(f"Payload size ({len(payload)}) exceeds 16KB bank limit ({BANK_SIZE})")
    if len(payload) < BANK_SIZE:
        payload = payload + bytes([0xFF] * (BANK_SIZE - len(payload)))

    offset = bank * BANK_SIZE
    out = bytearray(base_data)
    out[offset:offset + BANK_SIZE] = payload
    return out


def build_forth_payload(forth_files, start_word="CIST-CLOCK"):
    tokens = []
    for fp in forth_files:
        raw = Path(fp).read_text(encoding="utf-8")
        cleaned = strip_forth_comments(raw, keep_blank_lines=False)
        for line in cleaned.splitlines():
            line = line.strip()
            if line:
                tokens.append(line)
    if start_word:
        tokens.append(start_word)
    payload = " ".join(tokens).encode("ascii")
    if len(payload) > 0x3FD0 - SRC_ADDR:
        raise ValueError(f"Forth source ({len(payload)} bytes) exceeds free ROM space")
    return payload


def build_16k_rom(base_forth_bytes, forth_payload):
    if len(base_forth_bytes) != 8192:
        raise ValueError(f"Expected 8192-byte base CamelForth ROM, got {len(base_forth_bytes)}")

    rom = bytearray(base_forth_bytes) + bytearray([0xFF] * 8192)
    rom[0x3FD0:0x4000] = rom[0x1FD0:0x2000]
    rom[SRC_ADDR:SRC_ADDR + len(forth_payload)] = forth_payload

    if struct.unpack_from("<H", rom, COLD_ABORT_XT)[0] != 0x1375:
        raise ValueError("Unexpected COLD layout in base CamelForth ROM")
    struct.pack_into("<H", rom, COLD_ABORT_XT, HOOK_ADDR)

    # Colon definition at HOOK_ADDR:
    # S0 SP! L0 LP ! R0 RP! 0 STATE ! <SRC_ADDR> <len> INTERPRET ABORT
    hook = b"\xcd\xa8\x02" + struct.pack(
        "<HHHHHHHHHHHHHHHHH",
        0x0AD7, 0x0480,                  # S0 SP!
        0x0AEE, 0x0ACC, 0x04B4,          # L0 LP !
        0x0AF9, 0x04A4,                  # R0 RP!
        0x028B, 0x0000, 0x0A8C, 0x04B4,  # 0 STATE !
        0x028B, SRC_ADDR,                # LIT SRC_ADDR
        0x028B, len(forth_payload),      # LIT len
        0x129C,                          # INTERPRET
        0x1375,                          # ABORT
    )
    rom[HOOK_ADDR:HOOK_ADDR + len(hook)] = hook
    return bytes(rom)


def main():
    parser = argparse.ArgumentParser(description="Build CamelForth + Cistercian Clock ROM image")
    parser.add_argument("--base-forth", type=Path, help="Optional 8KB CamelForth binary (default: extracted from factory HEX Bank 4)")
    parser.add_argument("--factory-hex", type=Path, default=DEFAULT_FACTORY_HEX, help="Mini II Factory Intel HEX image (default: %(default)s)")
    parser.add_argument("--bank", type=int, default=4, help="Target 16KB bank in Mini II 128KB ROM (0-7, default: 4 [CamelForth slot])")
    parser.add_argument("--start-word", default="CIST-CLOCK", help="Word to auto-run at boot (default: CIST-CLOCK, use '' for none)")
    parser.add_argument("--out-rom", type=Path, default=ROOT / "build" / "camelforth_clock.rom", help="Output 16KB ROM payload")
    parser.add_argument("--out-bin", type=Path, default=ROOT / "build" / "Mini_II_camelforth_clock.bin", help="Output 128KB Mini II .bin")
    parser.add_argument("--out-hex", type=Path, default=ROOT / "build" / "Mini_II_camelforth_clock.hex", help="Output 128KB Mini II .hex")
    args = parser.parse_args()

    factory_data = None
    if args.factory_hex.is_file():
        factory_data = parse_intel_hex(args.factory_hex)

    if args.base_forth and args.base_forth.is_file():
        base_forth = args.base_forth.read_bytes()
    elif factory_data is not None:
        base_forth = bytes(factory_data[4 * BANK_SIZE:4 * BANK_SIZE + 8192])
    else:
        sys.exit(f"Neither --base-forth nor --factory-hex ({args.factory_hex}) found.")

    payload = build_forth_payload(DEFAULT_FILES, start_word=args.start_word)
    rom_16k = build_16k_rom(base_forth, payload)

    args.out_rom.parent.mkdir(parents=True, exist_ok=True)
    args.out_rom.write_bytes(rom_16k)
    print(f"Wrote 16KB CamelForth payload: {args.out_rom} ({len(payload)} bytes Forth source at 0x{SRC_ADDR:04X})")

    if factory_data is not None:
        stitched = insert_bank(factory_data, rom_16k, args.bank)
        args.out_bin.parent.mkdir(parents=True, exist_ok=True)
        args.out_bin.write_bytes(stitched)
        args.out_hex.parent.mkdir(parents=True, exist_ok=True)
        write_intel_hex(stitched, args.out_hex)
        print(f"Wrote 128KB Mini II binary (Bank {args.bank}): {args.out_bin}")
        print(f"Wrote 128KB Mini II Intel HEX (Bank {args.bank}): {args.out_hex}")


if __name__ == "__main__":
    main()

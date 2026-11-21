#!/usr/bin/env python3
"""
cross_compile.py - Cross-compiler for RC2014 Z80 CamelForth.

Compiles Forth source files against the base 8KB CamelForth ROM dictionary into a
relocated RAM dictionary image (0x8800..HERE) plus updated DP and LATEST pointers.
Can output:
  - Raw binary RAM image (--out-bin)
  - Intel HEX image for 0x8800 + user area DP/LATEST or HEXLOAD snippet (--out-hex, --out-forth)
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

DICT_ORG = 0x8800
U0_ADDR = 0x8300
DP_USER_ADDR = U0_ADDR + 0x08      # 0x8308
LATEST_USER_ADDR = U0_ADDR + 0x0E  # 0x830E
UINIT_PFA = 0x0B0A                 # Offset in 8KB ROM of UINIT table

CF_DOCOLON = b"\xcd\xa8\x02"       # CALL 0x02A8
CF_DOCREATE = b"\xcd\xd4\x02"      # CALL 0x02D4
CF_DOCON = b"\xcd\xf4\x02"         # CALL 0x02F4


def load_base_rom(base_forth=None, factory_hex=DEFAULT_FACTORY_HEX):
    if base_forth and Path(base_forth).is_file():
        data = Path(base_forth).read_bytes()
        if len(data) < 8192:
            raise ValueError(f"Base Forth ROM too small: {len(data)} bytes")
        return data[:8192]
    if factory_hex and Path(factory_hex).is_file():
        raw = bytearray([0xFF] * 131072)
        base = 0
        with open(factory_hex, "r", encoding="latin1") as f:
            for line in f:
                line = line.strip()
                if not line.startswith(":"):
                    continue
                bc = int(line[1:3], 16)
                addr = int(line[3:7], 16)
                rtype = int(line[7:9], 16)
                if rtype == 0:
                    for i in range(bc):
                        target = base + addr + i
                        if target < len(raw):
                            raw[target] = int(line[9 + i * 2:11 + i * 2], 16)
                elif rtype == 4:
                    base = int(line[9:13], 16) << 16
                elif rtype == 1:
                    break
        return bytes(raw[4 * 16384:4 * 16384 + 8192])
    raise FileNotFoundError("Neither --base-forth nor factory HEX found")


def extract_rom_dictionary(rom_8k):
    dp0, _, _, latest0 = struct.unpack_from("<HHHH", rom_8k, UINIT_PFA + 8)
    words = {}
    nfa = latest0
    while nfa != 0:
        link = struct.unpack_from("<H", rom_8k, nfa - 3)[0]
        immed = rom_8k[nfa - 1] != 0
        length = rom_8k[nfa] & 0x7F
        name = rom_8k[nfa + 1:nfa + 1 + length].decode("ascii")
        cfa = nfa + 1 + length
        if name not in words:
            words[name] = (cfa, immed, nfa)
        nfa = link
    return words, dp0, latest0


def write_intel_hex_records(segments, hex_path):
    with open(hex_path, "w", encoding="latin1") as f:
        for base_addr, data in segments:
            for offset in range(0, len(data), 16):
                chunk = data[offset:offset + 16]
                addr = (base_addr + offset) & 0xFFFF
                cksum = (-(len(chunk) + (addr >> 8) + (addr & 0xFF) + sum(chunk))) & 0xFF
                hex_bytes = "".join(f"{b:02X}" for b in chunk)
                f.write(f":{len(chunk):02X}{addr:04X}00{hex_bytes}{cksum:02X}\n")
        f.write(":00000001FF\n")


class CamelForthCrossCompiler:
    def __init__(self, rom_8k, org=DICT_ORG):
        self.rom = rom_8k
        self.words, self.org, self.latest = extract_rom_dictionary(rom_8k)
        if org != self.org:
            self.org = org
        self.ram = bytearray()
        self.base = 10
        self.state = 0
        self.stack = []
        self.cs_stack = []
        self.leave_stack = []

    @property
    def here(self):
        return self.org + len(self.ram)

    def allot(self, n):
        if n > 0:
            self.ram.extend(b"\x00" * n)
        elif n < 0:
            del self.ram[n:]

    def c_comma(self, val):
        self.ram.append(val & 0xFF)

    def comma(self, val):
        self.ram.extend(struct.pack("<H", val & 0xFFFF))

    def store16(self, addr, val):
        offset = addr - self.org
        if not (0 <= offset <= len(self.ram) - 2):
            raise ValueError(f"Address 0x{addr:04X} outside compiled RAM dictionary")
        struct.pack_into("<H", self.ram, offset, val & 0xFFFF)

    def store8(self, addr, val):
        offset = addr - self.org
        if not (0 <= offset <= len(self.ram) - 1):
            raise ValueError(f"Address 0x{addr:04X} outside compiled RAM dictionary")
        self.ram[offset] = val & 0xFF

    def fetch16(self, addr):
        offset = addr - self.org
        return struct.unpack_from("<H", self.ram, offset)[0]

    def create_header(self, name, cf_bytes, immed=False):
        name_bytes = name.encode("ascii")
        if len(name_bytes) > 31:
            raise ValueError(f"Word name too long: {name}")
        self.comma(self.latest)
        self.c_comma(1 if immed else 0)
        nfa = self.here
        self.c_comma(len(name_bytes))
        self.ram.extend(name_bytes)
        cfa = self.here
        self.ram.extend(cf_bytes)
        self.latest = nfa
        self.words[name] = (cfa, immed, nfa)
        return cfa

    def parse_number(self, tok):
        s = tok
        neg = False
        if s.startswith("-"):
            neg = True
            s = s[1:]
        try:
            val = int(s, self.base)
        except ValueError:
            return None
        if neg:
            val = -val
        return val & 0xFFFF

    def xt(self, name):
        return self.words[name][0]

    def compile_source(self, source_text):
        cleaned = strip_forth_comments(source_text, keep_blank_lines=False)
        i = 0
        n = len(cleaned)

        def next_token(delim=None):
            nonlocal i
            if delim is None:
                while i < n and cleaned[i].isspace():
                    i += 1
                if i >= n:
                    return None
                start = i
                while i < n and not cleaned[i].isspace():
                    i += 1
                return cleaned[start:i]
            else:
                if i < n and cleaned[i] == " ":
                    i += 1
                start = i
                idx = cleaned.find(delim, i)
                if idx == -1:
                    i = n
                    return cleaned[start:]
                i = idx + 1
                return cleaned[start:idx]

        while True:
            tok = next_token()
            if tok is None:
                break

            if self.state == 0:
                if tok == "HEX":
                    self.base = 16
                elif tok == "DECIMAL":
                    self.base = 10
                elif tok == ":":
                    name = next_token()
                    self.create_header(name, CF_DOCOLON)
                    self.state = 1
                elif tok == "CREATE":
                    name = next_token()
                    cfa = self.create_header(name, CF_DOCREATE)
                    self.words[name] = (cfa, False, self.latest, "CREATE", self.here)
                elif tok == "VARIABLE":
                    name = next_token()
                    cfa = self.create_header(name, CF_DOCREATE)
                    pfa = self.here
                    self.comma(0)
                    self.words[name] = (cfa, False, self.latest, "VARIABLE", pfa)
                elif tok == "CONSTANT":
                    name = next_token()
                    val = self.stack.pop()
                    cfa = self.create_header(name, CF_DOCON)
                    self.comma(val)
                    self.words[name] = (cfa, False, self.latest, "CONSTANT", val)
                elif tok == "ALLOT":
                    count = self.stack.pop()
                    if count & 0x8000:
                        count -= 0x10000
                    self.allot(count)
                elif tok == "C,":
                    self.c_comma(self.stack.pop())
                elif tok == ",":
                    self.comma(self.stack.pop())
                elif tok == "!":
                    addr = self.stack.pop()
                    val = self.stack.pop()
                    self.store16(addr, val)
                elif tok == "C!":
                    addr = self.stack.pop()
                    val = self.stack.pop()
                    self.store8(addr, val)
                elif tok == "@":
                    addr = self.stack.pop()
                    self.stack.append(self.fetch16(addr))
                elif tok == "IMMEDIATE":
                    self.ram[self.latest - self.org - 1] = 1
                    for k, v in list(self.words.items()):
                        if v[2] == self.latest:
                            self.words[k] = (v[0], True) + v[2:]
                elif tok in self.words:
                    entry = self.words[tok]
                    if len(entry) >= 5 and entry[3] in ("VARIABLE", "CREATE"):
                        self.stack.append(entry[4])
                    elif len(entry) >= 5 and entry[3] == "CONSTANT":
                        self.stack.append(entry[4])
                    else:
                        raise ValueError(f"Unsupported interpret-mode execution of '{tok}'")
                else:
                    num = self.parse_number(tok)
                    if num is None:
                        raise ValueError(f"Unknown word or number in interpret mode: '{tok}'")
                    self.stack.append(num)
            else:
                # Compile mode (STATE = 1)
                if tok == ";":
                    self.comma(self.xt("EXIT"))
                    self.state = 0
                elif tok == "[":
                    self.state = 0
                elif tok == "]":
                    self.state = 1
                elif tok == "IF":
                    self.comma(self.xt("?branch"))
                    self.cs_stack.append(("IF", self.here))
                    self.comma(self.here)
                elif tok == "ELSE":
                    kind, orig = self.cs_stack.pop()
                    if kind != "IF":
                        raise ValueError("ELSE without matching IF")
                    self.comma(self.xt("branch"))
                    else_orig = self.here
                    self.comma(self.here)
                    self.store16(orig, self.here)
                    self.cs_stack.append(("ELSE", else_orig))
                elif tok == "THEN":
                    kind, orig = self.cs_stack.pop()
                    if kind not in ("IF", "ELSE", "WHILE"):
                        raise ValueError(f"THEN incompatible with {kind}")
                    self.store16(orig, self.here)
                elif tok == "BEGIN":
                    self.cs_stack.append(("BEGIN", self.here))
                elif tok == "WHILE":
                    self.comma(self.xt("?branch"))
                    self.cs_stack.append(("WHILE", self.here))
                    self.comma(self.here)
                elif tok == "REPEAT":
                    w_kind, w_orig = self.cs_stack.pop()
                    b_kind, b_dest = self.cs_stack.pop()
                    if w_kind != "WHILE" or b_kind != "BEGIN":
                        raise ValueError("Malformed BEGIN..WHILE..REPEAT")
                    self.comma(self.xt("branch"))
                    self.comma(b_dest)
                    self.store16(w_orig, self.here)
                elif tok == "UNTIL":
                    b_kind, b_dest = self.cs_stack.pop()
                    if b_kind != "BEGIN":
                        raise ValueError("UNTIL without matching BEGIN")
                    self.comma(self.xt("?branch"))
                    self.comma(b_dest)
                elif tok == "AGAIN":
                    b_kind, b_dest = self.cs_stack.pop()
                    if b_kind != "BEGIN":
                        raise ValueError("AGAIN without matching BEGIN")
                    self.comma(self.xt("branch"))
                    self.comma(b_dest)
                elif tok == "DO":
                    self.comma(self.xt("(do)"))
                    self.cs_stack.append(("DO", self.here))
                    self.leave_stack.append([])
                elif tok in ("LOOP", "+LOOP"):
                    d_kind, d_dest = self.cs_stack.pop()
                    if d_kind != "DO":
                        raise ValueError(f"{tok} without matching DO")
                    self.comma(self.xt("(loop)" if tok == "LOOP" else "(+loop)"))
                    self.comma(d_dest)
                    for l_orig in self.leave_stack.pop():
                        self.store16(l_orig, self.here)
                elif tok == "LEAVE":
                    self.comma(self.xt("UNLOOP"))
                    self.comma(self.xt("branch"))
                    self.leave_stack[-1].append(self.here)
                    self.comma(self.here)
                elif tok in ('S"', '."', 'ABORT"'):
                    s = next_token('"')
                    s_bytes = s.encode("ascii")
                    self.comma(self.xt('(S")'))
                    self.c_comma(len(s_bytes))
                    self.ram.extend(s_bytes)
                    if tok == '."':
                        self.comma(self.xt("TYPE"))
                    elif tok == 'ABORT"':
                        self.comma(self.xt("?ABORT"))
                elif tok == "[']":
                    w = next_token()
                    self.comma(self.xt("LIT"))
                    self.comma(self.xt(w))
                elif tok == "[CHAR]":
                    w = next_token()
                    self.comma(self.xt("LIT"))
                    self.comma(ord(w[0]))
                elif tok == "RECURSE":
                    # Current word is at self.latest
                    length = self.ram[self.latest - self.org] & 0x7F
                    self.comma(self.latest + 1 + length)
                elif tok in self.words:
                    cfa, immed = self.words[tok][0], self.words[tok][1]
                    if immed:
                        raise ValueError(f"Unhandled immediate word in compile mode: '{tok}'")
                    self.comma(cfa)
                else:
                    num = self.parse_number(tok)
                    if num is None:
                        raise ValueError(f"Unknown word or number in compile mode: '{tok}'")
                    self.comma(self.xt("LIT"))
                    self.comma(num)

        if self.state != 0:
            raise ValueError("Unclosed colon definition at end of input")
        if self.cs_stack:
            raise ValueError(f"Unbalanced control flow stack: {self.cs_stack}")


def cross_compile_files(forth_files, rom_8k=None, org=DICT_ORG):
    if rom_8k is None:
        rom_8k = load_base_rom()
    cc = CamelForthCrossCompiler(rom_8k, org=org)
    for fp in forth_files:
        cc.compile_source(Path(fp).read_text(encoding="utf-8"))
    return cc


def main():
    parser = argparse.ArgumentParser(description="Cross-compile Forth files for RC2014 CamelForth")
    parser.add_argument("files", nargs="+", type=Path, help="Forth source files to compile")
    parser.add_argument("--base-forth", type=Path, help="8KB base CamelForth ROM binary")
    parser.add_argument("--factory-hex", type=Path, default=DEFAULT_FACTORY_HEX, help="Mini II factory Intel HEX")
    parser.add_argument("--out-bin", type=Path, default=ROOT / "build" / "forth_ram.bin", help="Output raw compiled RAM dictionary binary (default: %(default)s)")
    parser.add_argument("--out-hex", type=Path, default=ROOT / "build" / "forth_ram.hex", help="Output Intel HEX file for HEXLOAD (default: %(default)s)")
    parser.add_argument("--no-user-vars", action="store_true", help="Omit 0x8308 (DP) and 0x830E (LATEST) records from --out-hex")
    args = parser.parse_args()

    rom_8k = load_base_rom(args.base_forth, args.factory_hex)
    cc = cross_compile_files(args.files, rom_8k=rom_8k)

    print(
        f"Cross-compiled {len(args.files)} file(s): {len(cc.ram)} bytes "
        f"(0x{cc.org:04X}..0x{cc.here:04X}, DP=0x{cc.here:04X}, LATEST=0x{cc.latest:04X})"
    )

    if args.out_bin:
        args.out_bin.parent.mkdir(parents=True, exist_ok=True)
        args.out_bin.write_bytes(cc.ram)
        print(f"Wrote RAM binary: {args.out_bin}")

    if args.out_hex:
        args.out_hex.parent.mkdir(parents=True, exist_ok=True)
        segments = [(cc.org, bytes(cc.ram))]
        if not args.no_user_vars:
            segments.append((DP_USER_ADDR, struct.pack("<H", cc.here)))
            segments.append((LATEST_USER_ADDR, struct.pack("<H", cc.latest)))
        write_intel_hex_records(segments, args.out_hex)
        print(f"Wrote Intel HEX (for CamelForth HEXLOAD): {args.out_hex}")


if __name__ == "__main__":
    main()

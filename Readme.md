# RC2014 CamelForth

Collection of Forth code written for [RC2014](https://rc2014.co.uk/) [CamelForth](https://github.com/juzzas/camelforth-z80-bootrom).

- **`RTC/`**: Driver for the DS1302 Real-Time Clock module (date, time, DST, NVRAM).
  https://z80kits.com/shop/ds1302-real-time-clock-module/
- **`matrix8x8/`**: Driver and graphics library for the RC2014 8x8 LED Matrix module (copyright © Sheila Dixon). (https://z80kits.com/shop/8x8-led-matrix-display-module/)
- **`cistercian_clock/`**: Cistercian numeral clock using RTC and matrix8x8.
  Inspired by ExtKits: https://extkits.co.uk/resources/cotmres/ (Check out the ExtKits Pico ROMWBW kit: https://extkits.co.uk/product/pico-romwbw/)

## Tools (`helpers/`)

- **`spool.py`**: Minifies and streams Forth source over serial with line-by-line pacing so CamelForth compiles code reliably without buffer overflow alongside an open minicom session.
- **`cross_compile.py`**: Cross-compiles Forth source files into a CamelForth RAM dictionary binary or Intel HEX image for `HEXLOAD`. See [doc/cross_compile.md](doc/cross_compile.md).
- **`build_rom.py`**: Builds a 16 KB CamelForth ROM bank and 128 KB RC2014 Mini II ROM image with pre-compiled Forth words. See [doc/build_rom.md](doc/build_rom.md).
- **`program_onerom.sh`**: Flashes the 128 KB Mini II ROM image to a connected OneROM (`SST39SF010`).

---

*Code and documentation written with AI assistance.*

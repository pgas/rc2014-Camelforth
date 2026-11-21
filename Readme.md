# RC2014 CamelForth

Collection of Forth code written for [RC2014](https://rc2014.co.uk/) [CamelForth](https://github.com/juzzas/camelforth-z80-bootrom).


- **`RTC/`**: Driver for the DS1302 Real-Time Clock module (date, time, DST, NVRAM).
  https://z80kits.com/shop/ds1302-real-time-clock-module/
- **`matrix8x8/`**: Driver and graphics library for the RC2014 8x8 LED Matrix module (copyright © Sheila Dixon). (https://z80kits.com/shop/8x8-led-matrix-display-module/)
- **`cistercian_clock/`**: Cistercian numeral clock using RTC and matrix8x8.
  Inspired by ExtKits: https://extkits.co.uk/resources/cotmres/ (Check out the ExtKits Pico ROMWBW kit: https://extkits.co.uk/product/pico-romwbw/

## Helpers & Tools (`helpers/`)

- **`strip_comments.py`**: Strips Forth comments (`\`, `(...)`) and blank lines into `minified/` (or stdout).
  
- **`spool.py`**: Cleans and streams Forth source over serial with line-by-line pacing so CamelForth compiles code reliably without buffer overflow alongside an open minicom session.
- **`helpers/cistercian_clock.py`**: CLI visualizer for Cistercian numerals on an 8x8 matrix (takes time, shows ASCII matrix and Forth test command).
- **`helpers/strip_comments.py`**: Strips Forth comments (`\`, `(...)`) and blank lines into `minified/` (or stdout).
- **`helpers/spool.py`**: Minifies and streams Forth source over serial with line-by-line pacing so CamelForth compiles code reliably without buffer overflow alongside an open minicom session.
- **`helpers/build_rom.py`**: Packs `RTC.f`, `matrix8x8.f`, and `cistercian_clock.f` into a bootable 16 KB CamelForth ROM bank and stitches it into a 128 KB RC2014 Mini II EEPROM image that auto-starts `CIST-CLOCK` on boot.

## Building a New Forth ROM

To build a custom 128 KB RC2014 Mini II ROM (or standalone 16 KB bank) with the Cistercian clock preloaded and auto-starting on boot, you need the factory Mini II image (`ROMs/Factory/Mini II v1.2.HEX`) from the official [RC2014 repository](https://github.com/RC2014Z80/RC2014) (or a custom [camelforth-z80-bootrom](https://github.com/juzzas/camelforth-z80-bootrom) binary):

```bash
./helpers/build_rom.py --factory-hex ../mini2/ROMs/Factory/Mini\ II\ v1.2.HEX
```

Outputs are written to `build/` (`camelforth_clock.rom`, `Mini_II_camelforth_clock.bin`, and `Mini_II_camelforth_clock.hex`). Use `--bank 5` to insert into empty Bank 5 instead of replacing stock CamelForth in Bank 4, or `--start-word ""` to preload the words without auto-starting the clock.

---

*Code and documentation written with AI assistance.*

# Cistercian 8x8 Clock for RC2014 CamelForth

A digital timekeeper implementing the 13th-century Cistercian numeral cipher on an RC2014 8x8 LED matrix display, driven by the DS1302 Real-Time Clock module.

See [specification.md](specification.md) for full architectural background and cipher geometry.

## Overview

The clock encodes 24-hour time (`HH:MM`) around a central vertical stem:
* **Top-Left (Cols 0-2, Rows 0-2)**: Minute Tens ($0-5$)
* **Top-Right (Cols 4-6, Rows 0-2)**: Minute Units ($0-9$)
* **Bottom-Left (Cols 0-2, Rows 5-7)**: Hour Tens ($0-2$)
* **Bottom-Right (Cols 4-6, Rows 5-7)**: Hour Units ($0-9$)
* **Column 3 (Stem)**: Continuously illuminated central stem
* **Column 7 (Status)**:
  * Rows 0-6: Weekday (Row 0 = Mon, Row 1 = Tue, ..., Row 6 = Sun)
  * Row 7: Daylight Saving Time (lit when active)

## Loading over Serial

Requires `RTC.f` and `matrix8x8.f`:

```bash
./helpers/spool.py RTC/RTC.f matrix8x8/matrix8x8.f cistercian_clock/cistercian_clock.f
```

## Building a Bootable ROM & `HEXLOAD` Image

```bash
./cistercian_clock/build_clock_rom.sh
```

## Words

- `CIST-CLOCK` `( -- )` - Runs the live clock continuously from the DS1302 RTC. Press Enter 3 times in the serial terminal to exit.
- `CIST-UPDATE` `( -- )` - Reads current time, date (computes weekday), and DST flag from RTC and renders to `DISPLAY-BUFFER`.
- `CIST-SET` `( hh mm dow dst -- )` - Renders arbitrary time and status into `DISPLAY-BUFFER`.
- `CIST-ROTATE` `( -- addr )` - Flag controlling 90° counterclockwise display rotation (default `1`; set `0 CIST-ROTATE !` for vertical stem).
- `.CIST` `( -- )` - ASCII art visualizer of current display buffer in the serial terminal.

## Python Visualizer

You can test and visualize any timestamp directly from your workstation:

```bash
# Current system time
./cistercian_clock/cistercian_clock.py

# Specific time
./cistercian_clock/cistercian_clock.py 12 26
./cistercian_clock/cistercian_clock.py 22:14 --dow 1 --dst 1
```

## Acknowledgments & Inspiration

Special thanks to **ExtKits** for the inspiration via their [Cipher of the Monks resource](https://extkits.co.uk/resources/cotmres/).

Looking to upgrade your RC2014? Check out the [ExtKits Pico ROMWBW Kit](https://extkits.co.uk/product/pico-romwbw/) — an excellent Raspberry Pi Pico-based ROM, RAM, and mass storage expansion board for the RC2014 bus!

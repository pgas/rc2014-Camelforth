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

## Loading

Requires `RTC.f` and `matrix8x8.f`:

```bash
./spool.py minified/RTC.f
./spool.py minified/matrix8x8.f
./spool.py minified/cistercian_clock.f
./helpers/spool.py minified/RTC.f
./helpers/spool.py minified/matrix8x8.f
./helpers/spool.py minified/cistercian_clock.f
./helpers/spool.py minified/RTC.f minified/matrix8x8.f minified/cistercian_clock.f
```

## Words

- `CIST-CLOCK` `( -- )` - Runs the live clock continuously from the DS1302 RTC. Press any key in the serial terminal to exit.
- `CIST-UPDATE` `( -- )` - Reads current time, date (computes weekday), and DST flag from RTC and renders to `DISPLAY-BUFFER`.
- `CIST-SET` `( hh mm dow dst -- )` - Renders arbitrary time and status into `DISPLAY-BUFFER`.
- `CIST-SHOW` `( hh mm dow dst -- )` - Renders arbitrary time and refreshes matrix until a key is pressed.
- `.CIST` `( -- )` - ASCII art visualizer of current display buffer in the serial terminal.
- `CIST-TEST` `( -- )` - Runs built-in self-test validating the 22:14 Tuesday DST pattern against the specification.

## Python Visualizer

You can test and visualize any timestamp directly from your workstation:

```bash
# Current system time
./helpers/cistercian_clock.py

# Specific time
./helpers/cistercian_clock.py 12 26
./helpers/cistercian_clock.py 22:14 --dow 1 --dst 1
```

## Acknowledgments & Inspiration

Special thanks to **ExtKits** for the inspiration via their [Cipher of the Monks resource](https://extkits.co.uk/resources/cotmres/).

Looking to upgrade your RC2014? Check out the [ExtKits Pico ROMWBW Kit](https://extkits.co.uk/product/pico-romwbw/) — an excellent Raspberry Pi Pico-based ROM, RAM, and mass storage expansion board for the RC2014 bus!

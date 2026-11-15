# RC2014 8x8 LED Matrix Display Library

A driver and graphics library for the RC2014 8x8 LED Matrix module in CamelForth.

- **Author**: Sheila Dixon (S Dixon) - [https://peacockmedia.software](https://peacockmedia.software)
- **Origin**: [8x8_matrix_toolbox](https://github.com/shieladixon/8x8_matrix_toolbox) (`forth/BINCL-RC.F`, `forth/MATRIXTB_ACE.F`, `assembly/8x8-template.asm`)
- **Copyright & License**: Copyright (c) Sheila Dixon. Provided as part of the 8x8 matrix toolbox for RC2014.

## Hardware Interface

The RC2014 8x8 LED Matrix module uses two I/O ports:
- **Port 00h (`ROW-PORT`)**: Selects the active row (active high bitmask: row 0 = 01h, row 7 = 80h).
- **Port 02h (`DATA-PORT`)**: Column pattern for the active row (active high: bit 7 = leftmost LED, bit 0 = rightmost LED).

Since the matrix relies on multiplexing, rows are scanned sequentially. Between rows, the column LEDs are momentarily blanked (`0 DATA-PORT PC!`) to prevent ghosting.

### Why Multiplexing & Refresh are Needed

The RC2014 8x8 matrix module is a direct, unbuffered LED array without a dedicated controller chip (like a MAX7219). At any given moment, the hardware can only physically light up one row.

To produce a visible 2D image, the system relies on **Persistence of Vision (POV)**:
1. The CPU draws pixels into an 8-byte buffer in RAM (`DISPLAY-BUFFER`).
2. The CPU continuously runs a refresh loop (`REFRESH`), sequentially illuminating rows 0 through 7 at high speed.
3. If the CPU stops refreshing, the display will go dark (or freeze on a single row).

### Example: Main Loop Drawing a Cross
### Example: Drawing a Cross (`cross.f`)

To display a pattern, draw to the buffer and run `REFRESH` in a loop:
To display a pattern, draw pixels into `DISPLAY-BUFFER` and refresh the matrix. 
To display a pattern, draw pixels into `DISPLAY-BUFFER` and enter a refresh loop. `KEY?` non-blockingly checks if a key has been pressed in the serial terminal:

On the RC2014 boot ROM, serial I/O is interrupt-driven (an ISR intercepts incoming characters into a RAM ring buffer, immediately clearing the UART's hardware status register). Polling the hardware port (`128 PC@`) therefore never sees the keypress. Instead, use `REFRESH-N` for timed displays:

```forth
\ Draw a diagonal cross (X)
: DRAW-CROSS ( -- )
  MATRIX-CLS
  8 0 DO
    I I XY1        \ bottom-left to top-right
    7 I - I XY1    \ top-left to bottom-right
  LOOP ;

\ Main display loop (exit by pressing any key in serial terminal)
\ Continuous refresh loop (press Reset to stop)
\ Main display loop: refreshes until any key is pressed in terminal
: MAIN ( -- )
\ Display cross for N refresh passes, then clear display
: SHOW-CROSS ( n -- )
  DRAW-CROSS
  BEGIN
    REFRESH
     128 PC@ 1 AND         \ read from serial 
  UNTIL DROP
  AGAIN ;
    128 PC@ 1 AND  \ poll serial: bit 0 set when key pressed
    KEY?
  UNTIL
  KEY DROP         \ consume key
  REFRESH-N
  KEY DROP         \ consume key so it is not interpreted
  MATRIX-CLS
  REFRESH ;

\ Main demo: displays cross for ~500 passes (~3-4 seconds) and returns
: MAIN ( -- )
  500 SHOW-CROSS ;
```

For a timed display without an infinite loop, use `REFRESH-N`:
For a continuous display running indefinitely until hardware Reset:

```forth
\ Display cross for N refresh passes (~500 passes is a few seconds)
\ Timed display for N refresh passes
: SHOW-CROSS ( n -- )
: CONTINUOUS ( -- )
  DRAW-CROSS
  REFRESH-N
  MATRIX-CLS
  REFRESH ;
  BEGIN
    REFRESH
  AGAIN ;
```

---

## Coordinate System

Cartesian coordinates with origin `(0, 0)` at bottom-left:
- **Columns (`col`)**: 0 to 7 (0 is leftmost column, 7 is rightmost column).
- **Rows (`row`)**: 0 to 7 (0 is bottom row, 7 is top row).

---

## Word Reference

### Drawing & Pixel Control
- `XY1` `( col row -- )` - Turns ON the pixel at `(col, row)`.
- `XY0` `( col row -- )` - Turns OFF the pixel at `(col, row)`.
- `XY-TOGGLE` `( col row -- )` - Toggles the pixel at `(col, row)`.
- `XY?` `( col row -- flag )` - Returns non-zero (true) if the pixel at `(col, row)` is lit.
- `ROW!` `( pattern row -- )` - Writes an 8-bit pattern directly to `row` (0=bottom, 7=top).
- `ROW@` `( row -- pattern )` - Reads the 8-bit pattern from `row`.

### Buffer Operations
- `MATRIX-CLS` `( -- )` - Clears the display buffer (turns off all LEDs).
- `MATRIX-FILL` `( -- )` - Fills the display buffer (turns on all LEDs).
- `MATRIX-INVERT` `( -- )` - Inverts all pixels in the display buffer.
- `DISPLAY-BUFFER` `( -- addr )` - Address of the 8-byte display buffer.

### Display Refresh & Multiplexing
- `REFRESH` `( -- )` - Performs one multiplexed refresh pass across all 8 rows.
- `REFRESH-N` `( n -- )` - Performs `n` multiplexed refresh passes.
- `ON-TIME` `( -- addr )` - Variable controlling row illumination duration (default 1; increase for higher CPU clocks).

### Diagnostics
- `PDB` or `.MATRIX` `( -- )` - Dumps the 8 raw buffer bytes to the console.


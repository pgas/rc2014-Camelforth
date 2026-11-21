\ cistercian_clock.f - Cistercian 8x8 Clock for RC2014 CamelForth
\ Combines DS1302 RTC and 8x8 LED matrix display to render time as Cistercian numerals.
\ Inspired by ExtKits: https://extkits.co.uk/resources/cotmres/
\ (Check out the ExtKits Pico ROMWBW kit: https://extkits.co.uk/product/pico-romwbw/)
\
\ Requires RTC.f and matrix8x8.f to be loaded first:
\   ./helpers/spool.py minified/RTC.f minified/matrix8x8.f minified/cistercian_clock.f
\
\ Quadrant layout:
\   Top-Left: Minute Tens (0-5)      | Center Stem (Col 3): Backbone
\   Top-Right: Minute Units (0-9)    | Status (Col 7):
\   Bottom-Left: Hour Tens (0-2)     |   Rows 0-6: Mon-Sun
\   Bottom-Right: Hour Units (0-9)   |   Row 7: DST active

DECIMAL

\ --- Digit Primitives (3 rows: outer, middle, inner) ---
\ Right Wing: Columns 4-6 (Bits 3, 2, 1)
CREATE CIST-RIGHT
  HEX
  00 C, 00 C, 00 C,  \ 0
  0E C, 00 C, 00 C,  \ 1
  00 C, 00 C, 0E C,  \ 2
  08 C, 04 C, 02 C,  \ 3
  02 C, 04 C, 08 C,  \ 4
  0E C, 02 C, 08 C,  \ 5
  02 C, 02 C, 02 C,  \ 6
  0E C, 02 C, 02 C,  \ 7
  02 C, 02 C, 0E C,  \ 8
  0E C, 02 C, 0E C,  \ 9
  DECIMAL

\ Left Wing: Columns 0-2 (Bits 7, 6, 5), horizontal mirror
CREATE CIST-LEFT
  HEX
  00 C, 00 C, 00 C,  \ 0
  E0 C, 00 C, 00 C,  \ 1
  00 C, 00 C, E0 C,  \ 2
  20 C, 40 C, 80 C,  \ 3
  80 C, 40 C, 20 C,  \ 4
  E0 C, 80 C, 20 C,  \ 5
  80 C, 80 C, 80 C,  \ 6
  E0 C, 80 C, 80 C,  \ 7
  80 C, 80 C, E0 C,  \ 8
  E0 C, 80 C, E0 C,  \ 9
  DECIMAL

: CIST-R@ ( digit row -- pattern )
  SWAP 3 * + CIST-RIGHT + C@ ;

: CIST-L@ ( digit row -- pattern )
  SWAP 3 * + CIST-LEFT + C@ ;

\ --- Calendar / Weekday Helper ---
\ Sakamoto month table (ISO weekday 0=Mon .. 6=Sun)
CREATE CIST-MONTHS 6 C, 2 C, 1 C, 4 C, 6 C, 2 C, 4 C, 0 C, 3 C, 5 C, 1 C, 3 C,

\ Computes day-of-week (0=Mon .. 6=Sun) from RTC date (dd mm yy)
: RTC-DOW@ ( -- dow )
  RTC-DATE@
  OVER 3 < IF 1 - THEN
  28 + DUP 4 / +
  SWAP 1 - CIST-MONTHS + C@ +
  + 7 MOD ;

\ --- Frame Rendering Helpers ---
: ROW-OR! ( pattern row -- )
  DISPLAY-BUFFER + DUP C@ ROT OR SWAP C! ;

: CIST-INIT ( -- )
  8 0 DO 16 I DISPLAY-BUFFER + C! LOOP ;

: SET-DOW ( dow -- )
  DUP 7 U< IF 1 SWAP ROW-OR! ELSE DROP THEN ;

: SET-DST ( dst -- )
  IF 1 7 ROW-OR! THEN ;

: CIST-WING-TOP ( m1 m0 -- )
  3 0 DO
    2DUP
    I CIST-R@ SWAP
    I CIST-L@ OR
    I ROW-OR!
  LOOP 2DROP ;

: CIST-WING-BOT ( h1 h0 -- )
  3 0 DO
    2DUP
    2 I - CIST-R@ SWAP
    2 I - CIST-L@ OR
    5 I + ROW-OR!
  LOOP 2DROP ;

\ Render specific time & status to DISPLAY-BUFFER
: CIST-SET ( hh mm dow dst -- )
  CIST-INIT
  SET-DST
  SET-DOW
  10 /MOD SWAP CIST-WING-TOP
  10 /MOD SWAP CIST-WING-BOT ;

\ --- State Variables ---
VARIABLE CUR-DOW
VARIABLE CUR-DST
VARIABLE LAST-MIN
VARIABLE CLOCK-TICKS

: CIST-SYNC-STATUS ( -- )
  RTC-DOW@ CUR-DOW !
  0 RTC-C@ CUR-DST ! ;

\ Full update from standard RTC driver
: CIST-UPDATE ( -- )
  CIST-SYNC-STATUS
  RTC-TIME@                  \ ss mm hh
  DUP 0= IF CIST-SYNC-STATUS THEN
  OVER LAST-MIN !
  SWAP CUR-DOW @ CUR-DST @   \ ss hh mm dow dst
  CIST-SET
  DROP ;

\ --- Terminal Visualizer ---
: .CIST ( -- )
  CR
  8 0 DO
    DISPLAY-BUFFER I + C@
    8 0 DO
      DUP 128 AND IF ." # " ELSE ." . " THEN
      1 LSHIFT
      I 2 = IF ." | " THEN
      I 3 = IF ." | " THEN
      I 6 = IF ." | " THEN
    LOOP
    DROP CR
  LOOP ;

\ --- Main Clock Loop ---
\ Live clock: checks RTC every ~2.5s directly against hardware (zero drift, zero flash)
: CIST-CLOCK ( -- )
  CIST-UPDATE
  0 CLOCK-TICKS !
  0
  BEGIN
    REFRESH
    CLOCK-TICKS @ 1 + DUP CLOCK-TICKS !
    2000 > IF
      0 CLOCK-TICKS !
      RTC-TIME@ DROP SWAP DROP   \ mm
      LAST-MIN @ <> IF
        CIST-UPDATE
      THEN
    THEN
    KEY? IF KEY 13 = IF 1 + ELSE DROP 0 THEN THEN
    DUP 2 >
  UNTIL
  DROP
  MATRIX-CLS
  REFRESH ;

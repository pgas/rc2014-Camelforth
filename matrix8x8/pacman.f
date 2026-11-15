\ pacman.f - 8x8 LED Matrix Pacman Example for RC2014 CamelForth
\ Demonstrates static display, in-place chomping, and horizontal animation.
\
\ Requires matrix8x8.f to be loaded first:
\   ./spool.py minified/matrix8x8.f
\   ./spool.py minified/pacman.f
\
\ Provided Words:
\   PACMAN-STATIC ( -- )      - Displays open-mouthed Pacman centered (~2 sec)
\   PACMAN-CHOMP  ( n -- )     - Chomps in place (alternates mouth) for n cycles
\   PACMAN-WALK   ( -- )      - Walks across screen once (left to right)
\   PACMAN-MOVE   ( n -- )     - Repeats PACMAN-WALK for n passes
\   PACMAN-DEMO   ( -- )      - Complete demonstration sequence
\   PACMAN-SPEED  ( -- addr ) - Variable: refresh frames per step (default 15)

DECIMAL

\ Animation speed: number of display refresh passes per animation frame
VARIABLE PACMAN-SPEED
15 PACMAN-SPEED !

\ Bitmaps: 8 bytes (Row 7 top to Row 0 bottom)
CREATE PACMAN-OPEN
  HEX
  3C C, 7E C, FC C, F0 C, F0 C, FC C, 7E C, 3C C,
  DECIMAL

CREATE PACMAN-CLOSED
  HEX
  3C C, 7E C, FF C, FF C, FF C, FF C, 7E C, 3C C,
  DECIMAL

: SHIFT-BYTE ( byte s -- byte' )
  DUP 0< IF
    NEGATE LSHIFT 255 AND
  ELSE
    RSHIFT 255 AND
  THEN ;

: DRAW-PACMAN-SHIFTED ( frame-addr s -- )
  8 0 DO
    OVER I + C@ OVER SHIFT-BYTE
    DISPLAY-BUFFER I + C!
  LOOP 2DROP ;

: PACMAN-OPEN-AT ( s -- )
  PACMAN-OPEN SWAP DRAW-PACMAN-SHIFTED ;

: PACMAN-CLOSED-AT ( s -- )
  PACMAN-CLOSED SWAP DRAW-PACMAN-SHIFTED ;

\ --- Static Display ---
\ Displays stationary open-mouthed Pacman for ~2 seconds
: PACMAN-STATIC ( -- )
  0 PACMAN-OPEN-AT
  60 PACMAN-SPEED @ * REFRESH-N ;

\ --- In-Place Chomp Animation ---
\ Chomps open and closed in the center of the display
: PACMAN-CHOMP ( n -- )
  BEGIN DUP WHILE
    0 PACMAN-OPEN-AT
    PACMAN-SPEED @ REFRESH-N
    0 PACMAN-CLOSED-AT
    PACMAN-SPEED @ REFRESH-N
    1 -
  REPEAT DROP ;

\ --- Moving Animation ---
\ Walks Pacman across the matrix from left to right once
: PACMAN-WALK ( -- )
  -8
  BEGIN DUP 9 < WHILE
    DUP 1 AND IF
      DUP PACMAN-CLOSED-AT
    ELSE
      DUP PACMAN-OPEN-AT
    THEN
    PACMAN-SPEED @ REFRESH-N
    1 +
  REPEAT DROP ;

\ Loops the walk across the screen n times
: PACMAN-MOVE ( n -- )
  BEGIN DUP WHILE
    PACMAN-WALK
    1 -
  REPEAT DROP ;

\ --- Full Demo ---
: PACMAN-DEMO ( -- )
  CR ." 8x8 LED Matrix Pacman Demo"
  CR ." 1. Static Pacman..."
  PACMAN-STATIC
  CR ." 2. Chomping in place..."
  6 PACMAN-CHOMP
  CR ." 3. Moving across screen..."
  3 PACMAN-MOVE
  MATRIX-CLS
  REFRESH
  CR ." Done!" CR ;

\ cross.f - 8x8 LED Matrix Cross Example for RC2014 CamelForth
\ Draws a diagonal cross (X) and runs a multiplexed refresh loop.
\ Exits when any key is pressed in the serial terminal.
\
\ Requires matrix8x8.f to be loaded first:
\   ./helpers/spool.py minified/matrix8x8.f
\   ./helpers/spool.py minified/cross.f

DECIMAL

\ Draw a diagonal cross (X)
: DRAW-CROSS ( -- )
  MATRIX-CLS
  8 0 DO
    I I XY1        \ bottom-left to top-right
    7 I - I XY1    \ top-left to bottom-right
  LOOP ;

\ Main display loop: refreshes until any key is pressed in terminal
: MAIN ( -- )
  DRAW-CROSS
  BEGIN
    REFRESH
    KEY?
  UNTIL
  KEY DROP         \ consume key so it is not interpreted
  MATRIX-CLS
  REFRESH ;

\ Timed display for N refresh passes
: SHOW-CROSS ( n -- )
  DRAW-CROSS
  REFRESH-N
  MATRIX-CLS
  REFRESH ;

\ 8x8 Matrix Display Library for RC2014
\ S Dixon https://peacockmedia.software
\ Source: https://github.com/shieladixon/8x8_matrix_toolbox
\ Adapted for RC2014 CamelForth
\
\ Hardware Configuration:
\   Port 00: Row select (active high, 1-of-8)
\   Port 02: Column data (active high, 8 bits)
\
\ Coordinate system:
\   Column 0..7 (0=left, 7=right)
\   Row 0..7 (0=bottom, 7=top)

0 CONSTANT ROW-PORT
2 CONSTANT DATA-PORT

VARIABLE ON-TIME
1 ON-TIME !

CREATE DISPLAY-BUFFER 0 C, 0 C, 0 C, 0 C, 0 C, 0 C, 0 C, 0 C,
CREATE TWOS 1 C, 2 C, 4 C, 8 C, 16 C, 32 C, 64 C, 128 C,
CREATE LTWOS 128 C, 64 C, 32 C, 16 C, 8 C, 4 C, 2 C, 1 C,

: POWER2 ( x -- mask )
  TWOS + C@ ;

: SEND-ROW ( data row -- )
  POWER2
  ROW-PORT PC!
  DATA-PORT PC! ;

: SENDDATATOROW ( data row -- )
  SEND-ROW ;

: DELAY ( n -- )
  BEGIN DUP WHILE 1 - REPEAT DROP ;

: REFRESH ( -- )
  8 0 DO
    DISPLAY-BUFFER I + C@
    I SEND-ROW
    ON-TIME @ DELAY
    0 DATA-PORT PC!
  LOOP ;

: REFRESH-N ( n -- )
  BEGIN DUP WHILE
    REFRESH
    1 -
  REPEAT DROP ;

: MATRIX-CLS ( -- )
  DISPLAY-BUFFER 8 0 FILL ;

: MATRIX-FILL ( -- )
  DISPLAY-BUFFER 8 255 FILL ;

: MATRIX-INVERT ( -- )
  8 0 DO
    DISPLAY-BUFFER I + DUP C@ 255 XOR SWAP C!
  LOOP ;

: XY1 ( col row -- )
  7 SWAP -
  DISPLAY-BUFFER + DUP C@
  ROT
  LTWOS + C@
  OR
  SWAP C! ;

: XY0 ( col row -- )
  7 SWAP -
  DISPLAY-BUFFER + DUP C@
  ROT
  LTWOS + C@
  255 SWAP -
  AND
  SWAP C! ;

: XY? ( col row -- flag )
  7 SWAP -
  DISPLAY-BUFFER + C@
  SWAP LTWOS + C@
  AND 0= INVERT ;

: XY-TOGGLE ( col row -- )
  7 SWAP -
  DISPLAY-BUFFER + DUP C@
  ROT
  LTWOS + C@
  XOR
  SWAP C! ;

: ROW! ( pattern row -- )
  7 SWAP - DISPLAY-BUFFER + C! ;

: ROW@ ( row -- pattern )
  7 SWAP - DISPLAY-BUFFER + C@ ;

: PDB ( -- )
  8 0 DO
    DISPLAY-BUFFER I + C@ .
  LOOP ;

: .MATRIX ( -- )
  PDB ;

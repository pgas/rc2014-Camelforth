HEX

\ -- Default value for the module --
\ RC2014 DS1302 RTC module (Ed Brindley design)
\ If switches 1-4 are LOW and switches 5-6 are HIGH/ON: port is 0C hex.
\ If switches 1-2 are HIGH/ON and switches 3-6 are LOW: port is C0 hex.
C0 CONSTANT RTC-PORT

\ --- Hardware Configuration ---
\ Write lines (Port C0):
\   D4: CE (Chip Enable / RST, Active High)
\   D5: /WE (Write Enable for 74HCT125 buffer, Active Low: 0=drive IO, 1=tri-state)
\   D6: SCLK (Serial Clock)
\   D7: DATA OUT (Data to DS1302)
10 CONSTANT MASK-CE
20 CONSTANT MASK-WE
40 CONSTANT MASK-SCLK
80 CONSTANT MASK-DATA-OUT

\ Read line (Port C0):
\   D0: DATA IN (Data from DS1302 via 74HCT125 buffer)
01 CONSTANT MASK-DATA-IN 

\ Quiescent / Idle state: CE=0, SCLK=0, /WE=1 (buffer tri-stated) -> 20 hex
VARIABLE RTC-STATE
20 RTC-STATE !

\ --- Low-Level Pin Control ---
: RTC-OUT ( -- )
  RTC-STATE @ RTC-PORT PC! ;

: SCLK-HI ( -- )
  MASK-SCLK RTC-STATE @ OR RTC-STATE ! RTC-OUT ;

: SCLK-LO ( -- )
  MASK-SCLK INVERT RTC-STATE @ AND RTC-STATE ! RTC-OUT ;

: RTC-START ( -- )
  10 RTC-STATE ! RTC-OUT ;  \ CE=1, /WE=0, SCLK=0

: RTC-END ( -- )
  20 RTC-STATE ! RTC-OUT ;  \ CE=0, /WE=1, SCLK=0

\ --- Synchronous Serial Shift ---
\ DS1302 samples data on the rising edge of SCLK.
\ SCLK is left HIGH at the end of shifting out a byte.
: SHIFT-OUT ( c -- )
  MASK-WE INVERT RTC-STATE @ AND RTC-STATE !  \ Ensure /WE=0 (driving bus)
  8 0 DO
    SCLK-LO
    DUP 1 AND IF
      MASK-DATA-OUT RTC-STATE @ OR
    ELSE
      MASK-DATA-OUT INVERT RTC-STATE @ AND
    THEN
    RTC-STATE ! RTC-OUT
    SCLK-HI
    1 RSHIFT
  LOOP
  DROP ;

\ DS1302 outputs next bit on the falling edge of SCLK.
\ Host reads bit while SCLK is low, then raises SCLK high.
: SHIFT-IN ( -- c )
  MASK-WE RTC-STATE @ OR RTC-STATE ! RTC-OUT  \ /WE=1 (tri-state host driver)
  0
  8 0 DO
    1 RSHIFT
    SCLK-LO
    RTC-PORT PC@ MASK-DATA-IN AND IF
      80 OR
    THEN
    SCLK-HI
  LOOP ;

\ --- Register Primitives ---
: RTC-READ ( cmd -- c )
  RTC-START
  SHIFT-OUT
  SHIFT-IN
  RTC-END ;

: RTC-WRITE ( c cmd -- )
  RTC-START
  SHIFT-OUT
  SHIFT-OUT
  RTC-END ;

\ --- Write Protection Helpers ---
: RTC-UNLOCK ( -- )
  00 8E RTC-WRITE ;

: RTC-LOCK ( -- )
  80 8E RTC-WRITE ;

\ --- Battery-Backed User NVRAM (31 Bytes: 00h - 1Eh) ---
\ Read byte from NVRAM address (0 - 30)
: RTC-C@ ( addr -- byte )
  1 LSHIFT C1 + RTC-READ ;

\ Write byte to NVRAM address (0 - 30)
: RTC-C! ( byte addr -- )
  RTC-UNLOCK
  1 LSHIFT C0 + RTC-WRITE
  RTC-LOCK ;

\ Dump all 31 bytes of NVRAM
: RTC-RAM. ( -- )
  BASE @ >R HEX
  CR ." DS1302 NVRAM (31 bytes):"
  1F 0 DO
    I 8 MOD 0= IF CR I . ." : " THEN
    I RTC-C@ .
  LOOP
  CR R> BASE ! ;

\ --- BCD Conversions (Assumes HEX base is active during compilation) ---
: BCD>BIN ( bcd -- bin )
  DUP 0F AND SWAP 4 RSHIFT 0A * + ;

: BIN>BCD ( bin -- bcd )
  0A /MOD 4 LSHIFT + ;

\ --- Initialization ---
: RTC-INIT ( -- )
  RTC-UNLOCK
  81 RTC-READ       \ Read current Seconds
  7F AND            \ Clear Clock Halt (Bit 7 of 81)
  80 RTC-WRITE      \ Write back to Seconds to start oscillator
  RTC-LOCK
  0 RTC-C@ 1 <> IF  \ Ensure DST NVRAM flag is sane (0 if uninitialized)
    0 0 RTC-C!
  THEN ;

\ --- Words to write standard binary values to the RTC ---
: RTC-SET-TIME ( hh mm ss -- )
  RTC-UNLOCK
  BIN>BCD 80 RTC-WRITE  \ Write seconds (and clear Clock Halt bit)
  BIN>BCD 82 RTC-WRITE  \ Write minutes
  BIN>BCD 84 RTC-WRITE  \ Write hours (forces 24-hr mode)
  RTC-LOCK ;

: RTC-SET-DATE ( yy mm dd -- )
  RTC-UNLOCK
  BIN>BCD 86 RTC-WRITE  \ Write date
  BIN>BCD 88 RTC-WRITE  \ Write month
  BIN>BCD 8C RTC-WRITE  \ Write year
  RTC-LOCK ;

\ --- Display Routines ---
\ Print 2-digit number with leading zero and trailing space
: .2 ( n -- )
  DUP 0A < IF ." 0" THEN . ;

\ Burst read time (internal hold register prevents 01:59:59 -> 02:00:00 race)
: RTC-TIME@ ( -- ss mm hh )
  RTC-START BF SHIFT-OUT
  SHIFT-IN 7F AND BCD>BIN    \ seconds
  SHIFT-IN 7F AND BCD>BIN    \ minutes
  SHIFT-IN 3F AND BCD>BIN    \ hours
  5 0 DO SHIFT-IN DROP LOOP  \ drain remaining burst bytes
  RTC-END ;

: .TIME ( -- )
  BASE @ >R DECIMAL
  RTC-TIME@
  CR ." Time (HH MM SS): "
  .2 .2 .2
  R> BASE ! ;

\ Burst read date
: RTC-DATE@ ( -- dd mm yy )
  RTC-START BF SHIFT-OUT
  3 0 DO SHIFT-IN DROP LOOP  \ skip sec, min, hr
  SHIFT-IN 3F AND BCD>BIN    \ date
  SHIFT-IN 1F AND BCD>BIN    \ month
  SHIFT-IN DROP              \ skip day-of-week
  SHIFT-IN BCD>BIN           \ year
  SHIFT-IN DROP              \ skip control / WP
  RTC-END ;

: .DATE ( -- )
  BASE @ >R DECIMAL
  RTC-DATE@
  CR ." Date (YYYY MM DD): 20"
  .2 .2 .2
  R> BASE ! ;

\ --- Daylight Saving Time (DST) ---
\ Shift hour by offset n (+1 or -1). Refuses across midnight (0-23 limit).
\ Range 0..23 (HEX 17): 18 U< handles both >=24 and underflow (<0)
: DST-ADJ ( n -- flag )
  85 RTC-READ 3F AND BCD>BIN +
  DUP 18 U< IF
    RTC-UNLOCK BIN>BCD 84 RTC-WRITE RTC-LOCK -1
  ELSE
    DROP CR ." Cannot shift DST across midnight" CR 0
  THEN ;

\ State-tracked DST switch (0 DST = off, 1 DST = on)
: DST ( f -- )
  DUP 0 RTC-C@ = IF
    ." DST is already " IF ." ON" ELSE ." OFF" THEN CR EXIT
  THEN
  DUP IF 1 ELSE -1 THEN DST-ADJ IF
    DUP 0 RTC-C!
    ." DST " IF ." activated (+1 hour)" ELSE ." deactivated (-1 hour)" THEN CR
  ELSE
    DROP
  THEN ;

: DST? ( -- )
  0 RTC-C@ 1 = IF ." DST is ON (+1 hr)" ELSE ." DST is OFF" THEN CR ;

DECIMAL

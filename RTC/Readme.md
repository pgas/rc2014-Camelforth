# RC2014 DS1302 RTC

Driver for the [RC2014 DS1302 RTC module](https://github.com/electrified/rc2014-ds1302-rtc) in CamelForth.

## Initial Setup

A new module or fresh battery powers up with the oscillator halted to preserve the battery in storage.
- Run `RTC-INIT` once after battery installation to start the clock oscillator and initialize NVRAM byte 0 (defaults DST to 0).
- Not needed on subsequent boots (the battery keeps the clock running continuously).
- Calling `RTC-SET-TIME` also clears the halt bit and starts the oscillator automatically.

## User Words

- `RTC-INIT` `( -- )` - One-time setup: starts oscillator (clears CH flag) and defaults DST to 0.
- `RTC-SET-TIME` `( hh mm ss -- )` - Sets current time in 24-hr format.
- `RTC-SET-DATE` `( yy mm dd -- )` - Sets current date (year, month, day).
- `.TIME` `( -- )` - Displays current time (`HH MM SS`).
- `.DATE` `( -- )` - Displays current date (`YYYY MM DD`).
- `DST` `( 0|1 -- )` - Sets DST (`0 DST` = standard time/-1h, `1 DST` = daylight time/+1h).
- `DST?` `( -- )` - Displays current DST state from NVRAM.
- `RTC-RAM.` `( -- )` - Hex dumps all 31 bytes of user NVRAM (00h-1Eh).
- `RTC-C@` `( addr -- byte )` - Reads byte from NVRAM address (0-30).
- `RTC-C!` `( byte addr -- )` - Writes byte to NVRAM address (0-30).

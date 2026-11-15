# RC2014 CamelForth

Collection of Forth code written for [RC2014](https://rc2014.co.uk/) [CamelForth](https://github.com/juzzas/camelforth-z80-bootrom).

## Libraries

- **`RTC/`**: Driver for the DS1302 Real-Time Clock module (date, time, DST, NVRAM).
- **`matrix8x8/`**: Driver and graphics library for the RC2014 8x8 LED Matrix module (copyright © Sheila Dixon).

## Tools

- **`strip_comments.py`**: Strips Forth comments (`\`, `(...)`) and blank lines into `minified/` (or stdout).
- **`spool.py`**: Minifies and streams Forth source over serial with line-by-line pacing so CamelForth compiles code reliably without buffer overflow alongside an open minicom session.

---

*Code and documentation written with AI assistance.*

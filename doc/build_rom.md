# Building & Flashing a Custom ROM (`build_rom.py`)

`helpers/build_rom.py` uses `cross_compile.py` to pre-compile Forth source files into the upper 8 KB (`0x2000`) of a 16 KB CamelForth ROM bank and stitches it into a 128 KB RC2014 Mini II image.

On boot, `COLD` copies the pre-compiled dictionary from `0x2000` to `0x8800` via `CMOVE` in ~1.5 ms and optionally executes `--start-word`.

## Usage

Requires the factory Mini II image (`ROMs/Factory/Mini II v1.2.HEX`) from the [RC2014 repository](https://github.com/RC2014Z80/RC2014) (or an 8 KB CamelForth binary via `--base-forth`):

```bash
./helpers/build_rom.py <files.f ...> [--start-word WORD]
```

Default outputs in `build/`:
- `camelforth.rom` — Standalone 16 KB CamelForth bank
- `Mini_II_camelforth.bin` — 128 KB Mini II binary image
- `Mini_II_camelforth.hex` — 128 KB Mini II Intel HEX image

### Options
- `--start-word WORD`: Word to auto-run at boot (default: none).
- `--bank N`: Target 16 KB bank in the 128 KB Mini II ROM (`0..7`, default: `4`).
- `--out-rom`, `--out-bin`, `--out-hex`: Override output paths.

### Example (Cistercian Clock)

```bash
./cistercian_clock/build_clock_rom.sh
```

## RC2014 Mini II Jumpers

- **Page Size (`8K / 16K`)**: Set to **`16K`** (remove the `1` / `A13` jumper if shared).
- **ROM Bank (`8 / 4 / 2 / 1`)**: Set **`8`** High (`1 0 0 0`) for default 16 KB Bank 4 (`0x10000`).

# Cross-Compiling Forth (`cross_compile.py`)

`helpers/cross_compile.py` compiles Forth source files on the host against the base 8 KB RC2014 CamelForth ROM (`v20230819`) dictionary, producing a pre-compiled RAM dictionary image anchored at `0x8800`.

## Usage

```bash
./helpers/cross_compile.py \
  --out-bin build/camelforth_clock_ram.bin \
  --out-hex build/camelforth_clock_ram.hex
./helpers/cross_compile.py <files.f ...> \
  --out-bin build/forth_ram.bin \
  --out-hex build/forth_ram.hex
./helpers/cross_compile.py <files.f ...>
```

By default it compiles `RTC/RTC.f`, `matrix8x8/matrix8x8.f`, and `cistercian_clock/cistercian_clock.f`. Pass custom `.f` files as positional arguments to compile a different set:
Example:
Default outputs in `build/`:
- `forth_ram.bin` — Raw compiled RAM dictionary binary (`0x8800..HERE`)
- `forth_ram.hex` — Intel HEX image (`0x8800..HERE` plus `DP` at `0x8308` and `LATEST` at `0x830E`)

```bash
./helpers/cross_compile.py RTC/RTC.f matrix8x8/matrix8x8.f --out-hex build/drivers.hex
./helpers/cross_compile.py RTC/RTC.f matrix8x8/matrix8x8.f cistercian_clock/cistercian_clock.f \
  --out-hex build/camelforth_clock_ram.hex
```
### Options
- `--out-bin PATH`: Override output binary path.
- `--out-hex PATH`: Override output Intel HEX path.
- `--no-user-vars`: Omit the `0x8308` (`DP`) and `0x830E` (`LATEST`) pointer records from the Intel HEX output.

## Loading via `HEXLOAD`

The `--out-hex` output contains:
- The compiled dictionary at `0x8800..HERE`
- `DP` (`HERE`) at `0x8308`
- `LATEST` (last word's Name Field Address) at `0x830E`

At a stock RC2014 CamelForth prompt, run:

```forth
HEXLOAD
```

Then send or paste the `.hex` file over serial. When `Done` prints, all compiled words are immediately active in the dictionary. Use `--no-user-vars` if you only want the `0x8800` dictionary data without the `0x8308`/`0x830E` pointer records.
Then send or paste the `.hex` file over serial. When `Done` prints, all compiled words are immediately active in the dictionary. Use `--no-user-vars` to omit the `0x8308`/`0x830E` pointer records.
Then send or paste `build/forth_ram.hex` over serial. When `Done` prints, all compiled words are immediately active in the dictionary.

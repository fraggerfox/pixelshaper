# Examples

Pixel-font projects. The first two are vendored snapshots of
the parent repositories where they were developed glyph by glyph against real
hardware (an 11-row FOSSASIA LED badge):

| Example | Donor | Family | ppem | Notes |
|---|---|---|---|---|
| `manjari-pixel/` | Manjari Regular (SMC) | ManjariPixel | 14 | Geometric, compact — largest em on 11 rows |
| `nupuram-pixel/` | Nupuram Dots (SMC) | NupuramPixel | 12 | Round, dotted design; the original experiment |
| `noto-malayalam-pixel/` | Noto Sans Malayalam (Google) | NotoMalayalamPixel | 9 | The USAGE.md walkthrough project; auto-trace only, no hand-tuning yet |

Run from the repo root:

```sh
uv run pixelshaper -C examples/manjari-pixel status
uv run pixelshaper -C examples/manjari-pixel build
uv run pixelshaper -C examples/manjari-pixel render "മലയാളം"
```

The `glyphs/` directories contain substantial hand-tuning (open counters,
compressed marks, redrawn conjunct stacks — `pixelshaper status` lists
which glyphs differ from a fresh auto-trace). The living projects remain
in their parent repositories; these snapshots track them loosely.

Both derived fonts are SIL OFL 1.1 (see `fonts/OFL.txt` in each); the
donors declare no Reserved Font Names, so the families carry the donor
names.

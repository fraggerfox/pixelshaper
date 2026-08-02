# Examples

Pixel-font projects. The first two are vendored snapshots of
the parent repositories where they were developed glyph by glyph against real
hardware (an 11-row FOSSASIA LED badge):

| Example | Donor | Family | ppem | Notes |
|---|---|---|---|---|
| `manjari-pixel/` | Manjari Regular (SMC) | ManjariPixel | 14 | Geometric, compact — largest em on 11 rows |
| `nupuram-pixel/` | Nupuram Dots (SMC) | NupuramPixel | 12 | Round, dotted design; the original experiment |
| `noto-malayalam-pixel/` | Noto Sans Malayalam (Google) | NotoMalayalamPixel | 9 | The USAGE.md walkthrough project; auto-trace only, no hand-tuning yet |
| `mukta-devanagari-pixel/` | Mukta Regular (Ek Type) | MuktaPixel | 9 | Devanagari — first non-Malayalam script; auto-trace only |

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

## Devanagari: `mukta-devanagari-pixel/`

The example that proves the pipeline is script-agnostic: **zero code
changes** were needed to go from Malayalam to Devanagari. 73 glyphs traced
from a corpus of the varnamala, the full matra series on क, common
conjuncts (क्ष त्र ज्ञ श्र द्ध द्य क्त स्त), reph/rakar words (कर्म
प्रेम धर्म) and real words (नमस्ते, भारत, दिल्ली, मुंबई).

```sh
uv run pixelshaper -C examples/mukta-devanagari-pixel render "नमस्ते"
```

Script-specific behaviour, all inherited from Mukta's own GSUB/GPOS:
the **shirorekha** (headline) renders as one continuous lit row with
letters hanging below it; ि reorders before its consonant; the conjuncts
form as ligature glyphs. At 9 ppem on 11 rows Mukta's stems trace to
single pixels at the default 0.35 threshold (unlike Noto, which needed
0.45). Auto-trace only so far — the expected hand-tuning targets are the
ि hook above the headline, the reph, rakar forms, and कृ's tail.

All derived fonts are SIL OFL 1.1 (see `fonts/OFL.txt` in each); the
donors declare no Reserved Font Names, so the families carry the donor
names.

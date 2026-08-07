# Converting a font, step by step

A complete walkthrough of turning an outline font into a hand-tunable
pixel font. Every output below is real, from converting **Noto Sans
Malayalam** (the `examples/noto-sans-malayalam-pixel/` project); substitute
your own donor and script throughout.

```sh
nix develop        # or: any env with the deps from pyproject.toml
```

## Step 0 — check the donor's license

Open the donor's OFL text (or dump name-table IDs 0/13/14) and look for a
**Reserved Font Name** declaration in the copyright line:

```
Copyright 2022 The Noto Project Authors (https://github.com/notofonts/malayalam)
```

No "with Reserved Font Name …" clause → you may use the donor's name in
your family (`NotoSansMalayalamPixel`). If an RFN *is* declared, pick a name
that doesn't contain it. Keep the donor's `OFL.txt` in `fonts/` — the
derivative stays OFL 1.1 and the copyright travels with it.

## Step 1 — scaffold the project

```
noto-sans-malayalam-pixel/
├── pixelshaper.toml
├── corpus.txt
└── fonts/
    ├── NotoSansMalayalam-Regular.ttf
    └── OFL.txt
```

`pixelshaper.toml` — leave `ppem` out for now, on purpose:

```toml
[donor]
file = "fonts/NotoSansMalayalam-Regular.ttf"

[output]
family = "NotoSansMalayalamPixel"
threshold = 0.35

[display]
strip_height = 11        # rows of your target display
```

`corpus.txt` — one entry per line. **The corpus is the coverage spec**:
lines are shaped with the donor, and whatever glyphs the shaper emits are
what gets traced. Start with the script's alphabet plus real words that
exercise conjuncts, vowel signs and marks:

```
അ ആ ഇ ഈ ഉ ഊ ... ള ഴ റ      # full alphabet
മലയാളം
സന്തോഷ്
വ്യക്തി
...
```

## Step 2 — trace

```
$ pixelshaper -C examples/noto-sans-malayalam-pixel trace
ppem not pinned; suggesting 9 (worst corpus string fits 11 rows). Pin it
in pixelshaper.toml to keep the grid stable.
  amlym.txt: 14x7 adv=13
  ...
60 glyphs needed: 60 traced, 0 kept (hand-edits preserved)
```

Three things happened:

1. **Shaping-driven discovery.** HarfBuzz shaped every corpus line; the 60
   glyphs that came out include conjunct ligatures no cmap entry reaches.
2. **The ppem suggestion** is the largest integer size at which the
   *worst single corpus line* fits your strip, each line on its own
   baseline. This number is donor physics: compact Manjari affords 14 on
   the same 11 rows; Noto's roomier marks allow only 9. If it disappoints,
   your options are a different donor, a curated corpus (drop the deepest
   stacks and hand-compress them later), or pinning higher and accepting
   clipping warnings as your hand-tuning worklist. Don't decide from this
   one number — `pixelshaper ppem` (below) shows the whole landscape.
3. Each glyph became `glyphs/<name>.txt` — files keyed by stable glyph
   *name*, so donor updates can't orphan your edits. Two freshly traced
   examples — the letter അ and the tiny anusvara ം:

   > ```
   > name: amlym
   > advance: 13
   > left: 0
   > top: 6
   >
   > ··············
   > ·●●●●●●●●●●●··
   > ●●·●·●·●●·●●●·
   > ●··●·●··●·●·●·
   > ●··●·●··●●··●·
   > ·●·●●●··●·●●●·
   > ··············
   > ```

   > ```
   > name: anusvaramlym
   > advance: 4
   > left: 0
   > top: 4
   >
   > ····
   > ●●●●
   > ●··●
   > ·●●●
   > ····
   > ```

   These are exactly what you'll hand-edit in Step 6 — the ●/· grid is
   the glyph, the header is its metrics.

### Pinning the ppem — survey the landscape first

Before writing the number into the toml, look at what you'd be choosing
between:

```
$ pixelshaper -C examples/noto-sans-malayalam-pixel ppem
donor: NotoSansMalayalam-Regular.ttf  upem 1000  strip 11 rows

self-scale ppem per corpus line (hardest first):
    9.3  ( 1180 units)  തലശ്ശേരി
    9.5  ( 1155 units)  അരശ്ശ്
    9.9  ( 1113 units)  വ്യക്തി
   10.3  ( 1070 units)  തിരുവനന്തപുരം
   12.2  (  903 units)  ഇഫാക്ല
   13.3  (  830 units)  സന്തോഷ്
   13.9  (  794 units)  അ ആ ഇ ഈ ഉ ഊ ഋ എ ഏ ഐ ഒ ഓ…
   14.3  (  767 units)  മലയാളം
   14.3  (  767 units)  കേരളം

suggestion (every corpus line fits):  9
glyph ceiling (tallest single glyph): 12.2  (shashamlym, 903 units)
tallest glyphs: shashamlym (903), kalamlym (903), ivowelsignmlym (843), yapostmlym (824), emlym (794)

candidate ppem -> corpus lines clipping (worst overflow):
    9  all fit
   10  3/9 clip  (worst +0.8px: തലശ്ശേരി)
   11  4/9 clip  (worst +2.0px: തലശ്ശേരി)
   12  4/9 clip  (worst +3.2px: തലശ്ശേരി)
   13  5/9 clip  (worst +4.3px: തലശ്ശേരി)
   14  7/9 clip  (worst +5.5px: തലശ്ശേരി)
   15  9/9 clip  (worst +6.7px: തലശ്ശേരി)
```

How to read it:

- **self-scale per line** is what per-message scaling would give each
  line on its own: easy words could enjoy 14+, but the ശ്ശ words drag
  the common grid down to 9. The spread between the top and bottom of
  this table is what a fixed grid costs you — and a corpus *curated away
  from the hard lines* would move the suggestion up.
- **glyph ceiling** is a hard limit: above 12.2 the ശ്ശ ligature itself
  no longer fits the strip, no matter how lines are placed. Candidates
  beyond the ceiling mean redrawing that glyph shorter by hand, not just
  nudging it.
- **The overflow table prices each candidate.** Pinning 10 costs three
  clipping lines at under a pixel each — very payable with small mark
  compressions. Pinning 14 costs 7/9 lines and +5.5 px — a redesign, not
  a touch-up. This is exactly the trade the Manjari example took (pinned
  14 against a suggestion of 10) and paid off across ~55 hand-edits.

The Noto example stays at the safe suggestion: **pin `ppem = 9`** in
`pixelshaper.toml`. Future corpus extensions must trace on the same
grid; unpinned re-traces after a corpus change could silently pick a
different size.

Re-running `trace` later only fills gaps: existing files are skipped
(`--force` overwrites everything — it destroys hand-edits, so almost
never what you want).

## Step 3 — status

```
$ pixelshaper -C examples/noto-sans-malayalam-pixel status
project: noto-sans-malayalam-pixel  donor: NotoSansMalayalam-Regular.ttf  family: NotoSansMalayalamPixel  ppem: 9
corpus entries: 6  glyphs needed: 60
traced: 60/60
hand-edited: 0
```

`status` re-traces each needed glyph in memory and diffs it against the
file, so "hand-edited" is detected, not recorded — after months of
tuning it reconstructs your ledger exactly (the Manjari example reports
54 hand-edited glyphs this way).

## Step 4 — build

```
$ pixelshaper -C examples/noto-sans-malayalam-pixel build
60 glyphs pixelized at 9ppem (1px = 111.1 units) -> build/NotoSansMalayalamPixel.ttf
```

The donor is copied; only the outlines of your traced glyphs are replaced
with pixel squares (1 px = upem/ppem units). Advances and every GPOS
coordinate are quantized to the grid — without that, pixel-aligned bases
would still get fractionally-placed vowel signs. `cmap`/GSUB/GPOS pass
through otherwise untouched, and the native size is stamped into the
unique-ID name record (`NotoSansMalayalamPixel-9px;derived-from-Noto Sans
Malayalam`) so downstream renderers can discover it.

## Step 5 — render

```
$ pixelshaper -C examples/noto-sans-malayalam-pixel render മലയാളം

=== മലയാളം  (42x11)  -> notosansmalayalampixel-0b10e86f.png ===
··········································
··········································
···●●●●··●●●··●··●●●●●··●·●●●··●●●●●······
···●·●·●·●··●·●·●··●··●·●●··●·●●●··●······
··●··●·●●●●●●·●·●··●··●·●···●·●·●·●●·●●●●·
··●·●··●●·····●··●·●·●··●●··●··●●··●·●··●·
··●●●●●●●●●●●●●··●●●●●●●··●●●··●●●●●··●●●·
······························●●··········
·······························●●●●●······
··········································
··········································
```

Rendering is **1-bit mono at the native ppem** — a correct pixel font
needs no anti-aliasing or thresholds; what you see is exactly what a
1-bit display shows. The PNG (strip_height rows, white-on-black) is ready
for whatever consumes your display — for a
[FOSSASIA LED badge](https://badgemagic.fossasia.org/):
[`lednamebadge.py`](https://github.com/fossasia/led-name-badge-ls32)
`-s 4 -m 0 build/<render>.png`.

Placement modes:

- default: each whitespace token gets **its own baseline** — a word with
  tall marks and a word with deep tails each use the full strip;
- `--shared`: one baseline for the whole string — use for alphabet runs,
  where per-word centring makes the row wave;
- `--gap N`: columns between words (10 reads well on a scrolling badge).

Watch for `WARNING: ink span … exceeds N rows; clipping` — that's not
noise, it's your worklist.

## Step 6 — the hand-edit loop (where the quality comes from)

Auto-tracing gets ~90% of the way; the rest is why the format is text.
A glyph file:

```
name: amlym
advance: 13
left: 0
top: 6

··············
·●●●●●●●●●●●··
●●·●·●·●●·●●●·
●··●·●··●·●·●·
●··●·●··●●··●·
·●·●●●··●·●●●·
··············

```

`top` is the grid's top edge relative to the baseline (edit it to shift
the glyph vertically); the `●`/`·` rows are the shape. The loop:

```
edit glyphs/<name>.txt  →  pixelshaper build  →  pixelshaper render "<word>"
                        →  look at it on the real display  →  repeat
```

Seconds per cycle, and a fix applies everywhere the glyph appears.
Heuristics distilled from the Malayalam examples:

- **Trim heads, not tails.** Rounded crowns absorb a merged row almost
  invisibly; descending swashes carry the letter's identity.
- **Marks are where the vertical budget goes.** Above-marks (curls,
  chandrakkala, reph) and below-signs (u-signs, ya/ra sub-forms, stacked
  geminates) routinely need 1–3 rows of compression to coexist on one
  strip. Compress the mark/stack, not the base letter.
- **Open the counters.** At small ppem the threshold fattens strokes and
  closes loops; deleting a wall pixel restores the letter's identity.
- Keep an eye on `status` — it lists exactly which glyphs you've touched.

## Extending coverage later

Add lines to `corpus.txt`, run `trace` again (same pinned ppem!), and
only the newly needed glyphs are traced; every hand-edit survives. New
conjuncts that arrive too tall announce themselves as clipping warnings
at render time.

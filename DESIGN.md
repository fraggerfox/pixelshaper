# pixelshaper — design document

Generalizing the [Manjari](https://git.planet-express.in/manjari-pixel)
and Nupuram pixel fonts into a pipeline for donor-agnostic,
script-agnostic pixel-font derivation. Written 2026-08-01, distilling two
weeks of hands-on work getting Malayalam onto an 11-row LED badge.

## 1. Goals

1. **One tool, many projects.** A `pixelshaper` CLI that turns any
   HarfBuzz-shapeable, monochrome, horizontal-layout OpenType font into a
   hand-tunable pixel font, driven by a per-project config + corpus.
2. **Shaping preserved, always.** `cmap`/GSUB/GPOS pass through from the
   donor untouched (GPOS quantized to the grid). This is the defining
   feature — everything else is replaceable.
3. **Text-art as source of truth.** Per-glyph plain-text bitmaps, editable
   in any editor, diffable in git. The hand-tuning ledger *is* the project.
4. **Self-describing output.** Native ppem stamped in the font (name-table
   ID 3 `-<N>px` convention today; real EBDT/EBLC strike later) so
   consumers can render pixel-true without out-of-band knowledge.

### Non-goals

- Color fonts, vertical layout (v1), Nastaliq-class diagonal baselines.
- A GUI. The text-art loop + any editor is the interface.
- Removing the per-script legibility floor. Pixelization + hand-tuning buys
  ~1 row below a font's natural floor; physics keeps the rest.

## 2. Terminology

The process is **shaping-aware pixelization**: shaping-driven subsetting →
rasterization → binarization → re-vectorization (pixel-square outlines) →
metric/anchor quantization → hand-tuning (functionally, delta-hinting in a
friendlier medium).

## 3. Architecture

### CLI (one package, subcommands)

```
pixelshaper trace    # donor + corpus -> glyphs/<name>.txt   (skip-existing)
pixelshaper build    # glyphs/ -> build/<Family>.ttf
pixelshaper render   # text -> terminal grid + PNG strip, at native ppem
pixelshaper status   # coverage report: corpus vs traced vs hand-edited
```

(Current equivalents: pixelize.py / compile_font.py / verify_render.py;
`status` is new.)

The CLI is a thin layer over a **modular library**: each stage lives in
its own module (`pixelshaper.trace`, `.build`, `.render`, `.status`,
plus shared `.glyphart` for the text-art format and `.donor` for font
loading), importable as plain functions. Consumers other than the CLI —
the LED simulator, a future web preview, tests — call the library
directly rather than shelling out.

### Per-project layout

```
myfont-pixel/
├── pixelshaper.toml     # the config (below)
├── corpus.txt           # one entry per line; defines glyph coverage
├── fonts/               # donor TTF(s) + OFL.txt
├── glyphs/<name>.txt    # text-art source of truth
└── build/               # compiled TTF + rendered PNGs (gitignored)
```

### Config (`pixelshaper.toml`)

```toml
[donor]
file = "fonts/Manjari-Regular.ttf"
# instance = { wght = 400 }        # variable fonts: pin before tracing

[output]
family = "ManjariPixel"            # check the donor's OFL: if it declares a
                                   # Reserved Font Name, the family must not
                                   # contain it. Manjari and Nupuram declare
                                   # none, so donor-based names are fine.
ppem = 14                          # pin explicitly; auto-suggest on trace
threshold = 0.35

[display]
strip_height = 11                  # rows of the target device
```

Replaces today's meta.json + in-script constants + remembered CLI flags
(the "pin --ppem or new glyphs land on the wrong grid" trap disappears).

### Key change vs the parents: glyph files keyed by NAME, not gid

Today's `NNNN_name.txt` keys on glyph index; donor updates renumber gids
and would orphan hand-edits. v1 keys on glyph name (`ml_lla.txt`,
`k1th1.txt`), resolving gid at build time. Migration script renames the
existing files.

### Carried over unchanged (proven in the parents)

- HarfBuzz corpus shaping for inventory discovery (finds every conjunct
  ligature no cmap entry reaches).
- Grayscale rasterize + per-glyph threshold (mono rasterization destroys
  dotted/thin designs; learned the hard way).
- Pixel-run → rectangle outlines; hmtx + GPOS anchor quantization.
- Name-table ppem stamp; family rename (respecting OFL Reserved Font
  Names where the donor declares them).
- Render modes: per-word baselines (default), `--shared` single baseline
  (alphabet strips), `--gap N`, span warnings on clipping.

## 4. Work items, tiered

**T1 — packaging + config (the bulk, mostly mechanical)**
pyproject console-script; subcommands; toml config; corpus file;
name-keyed glyphs + migration; `status` subcommand.

**T2 — donor robustness**
Variable-font instancing (fontTools instancer); CFF/OTF donors via
cu2qu-based conversion (or documented fontmake pre-step in v1.0);
`vmtx` quantization when present.

**T3 — ecosystem (optional, post-v1)**
Emit real EBDT/EBLC strike alongside outlines; yaff import/export
(monobit interop); optionally delegate build to pixel-font-builder;
document the hand-tuning heuristics as a proper guide.

## 5. Example projects (migration of the parents)

manjari-pixel and nupuram-pixel become `examples/` consumers of the
installed tool: their scripts deleted, their `glyphs/` (renamed to
name-keys), corpus, and fonts kept, each gaining a `pixelshaper.toml`.
Their git history stays in their own repos; pixelshaper vendors a snapshot
or submodules them — decide at migration time. All hand-edits survive
(that's the point of the skip-existing rule and name keying). Since
neither donor declares an OFL RFN, the families are renamed at migration:
ManjaPixel → **ManjariPixel**, MalaPixel → **NupuramPixel**.

## 6. New use case: Devanagari

The first non-Malayalam validation target. Candidate OFL donors:

| Donor | Foundry | Why |
|---|---|---|
| **Mukta** | EkType | Clean, open forms; large conjunct set; the Manjari-analog |
| Hind | ITF | Compact UI font — likely affords a big ppem like Manjari did |
| Noto Sans Devanagari | Google | Baseline/reference behavior |
| Lohit Devanagari | Fedora | Minimal conjunct model (more halant forms = fewer glyphs to tune) |

Script-specific expectations (the "hand-tuning ledger" preview):

- **The shirorekha (headline) is a gift.** Devanagari's connecting top bar
  is a horizontal stroke — trivially pixel-perfect, and it gives every
  glyph a shared alignment row. But it must be *exactly* the same row in
  every glyph or joins show seams (same discipline as box-drawing chars);
  a `status`/lint check "headline row consistent across glyphs" is cheap
  and worth building.
- **Letters hang from the line** rather than sit on a baseline — the
  vertical budget splits differently than Malayalam (headline + body
  below + matras above the line + descenders/rakar below).
- **Known compression targets** (Malayalam analogs in parentheses):
  ि pre-base matra with its hook over the headline (ി curl); reph र् and
  candrabindu above (chandrakkala); rakar ्र and stacked conjuncts like
  द्ध, ट्ट below (്യ hook, ശ്ശ stack); nukta dots near the floor.
- **Floor estimate:** body ~0.5 em below the line plus above/below marks
  suggests a ~12–14 ppem native size on an 11-row strip with per-word
  baselines — to be measured with the real span data, as always.

Corpus starter: full varnamala, matra series on क, common conjuncts
(क्ष त्र ज्ञ श्र द्ध द्य), reph/rakar words (कर्म प्रेम), a name, a place
(दिल्ली), and the classic pangram-ish sampler once chosen.

## 7. Decisions

- **Tool license: BSD 2-Clause** (derived fonts remain OFL 1.1).
- **Canonical repo: `fraggerfox/pixelshaper` on GitHub**, standalone,
  with the LED badge as one consumer.
- **Simulator upstreaming** (native-ppem rendering + scaling toggle →
  santhoshtr/malayalam-led-simulator PR, referencing the stamp
  convention): yes, but only after this project is complete.
- **Strike emission (EBDT/EBLC)**: deferred past v1; revisit when a
  consumer besides the badge/simulator appears.

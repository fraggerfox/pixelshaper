# CLAUDE.md — pixelshaper

Shaping-aware pixel fonts: derive hand-tunable pixel fonts from OpenType
donors, keeping cmap/GSUB/GPOS intact. Read `README.md` for the concept,
`USAGE.md` for the conversion walkthrough, `DESIGN.md` for architecture
decisions and the work-item tiers.

## Layout

```
pixelshaper/          the library (CLI = thin wrapper, keep it that way)
  config.py           pixelshaper.toml + corpus.txt -> Project
  glyphart.py         ●/· text-art format, NAME-keyed files
  donor.py            fontTools+FreeType+HarfBuzz wrapper
  trace.py            donor+corpus -> glyphs/*.txt (skip-existing)
  build.py            glyphs/ -> build/<Family>.ttf
  render.py           native-ppem 1-bit render -> terminal + PNG
  status.py           coverage report (hand-edit detection)
  ppem.py             sizing report (self-scale per line, glyph ceiling)
  cli.py              pixelshaper -C <project> {trace,build,render,status,ppem}
examples/             manjari-pixel (54 hand-edits), nupuram-pixel,
                      noto-sans-malayalam-pixel (raw auto-trace, USAGE subject)
```

Dev shell: `nix develop` (uv + native libs). Run everything as
`uv run pixelshaper -C examples/<name> <subcommand>`.

## Invariants — do not break these

- **Shaping passes through.** build replaces glyph outlines, quantizes
  hmtx + GPOS coordinates to the pixel grid, rewrites family name records
  and the ppem stamp — nothing else in the donor changes.
- **Glyph files are keyed by glyph NAME**, never gid (gids shift across
  donor versions and orphan hand-edits). Filename = sanitized name;
  header `name:` is authoritative.
- **trace skips existing files.** Hand-edits are the project's value;
  `--force` destroys them and is only safe when `status` shows
  `hand-edited: 0`.
- **ppem must stay pinned** in pixelshaper.toml once glyphs exist. New
  glyphs traced at a different ppem silently land on the wrong grid.
- The output is only correct at its native ppem; the `-<N>px` stamp in
  name-table ID 3 is how consumers discover it. Keep writing it.

## Physics cheat-sheet (for advising on quality issues)

- Suggested ppem = strip_height x upem / worst-corpus-line span. It is a
  property of the donor's proportions: Manjari 14, Nupuram 12, Noto 9 on
  the same 11 rows.
- Strokes fatten/fuse -> threshold too low for this donor+ppem (sub-pixel
  stems light two columns). Strokes break -> too high. Sweep 0.35-0.65;
  Manjari 0.35@14, Noto 0.45@9, Nupuram-Dots 0.25@12 (dotted strokes).
- Render clipping warnings are the hand-tuning worklist: compress marks
  and stacks, not base letters; trim glyph heads, not tails.

## Working conventions

- Validate pipeline changes with a golden diff: render the full corpus of
  an example before/after and diff the ●/· rows — output must be
  pixel-identical unless the change intends otherwise.
- Family naming: check the donor's OFL for Reserved Font Names before
  using the donor's name (Manjari/Nupuram/Noto Malayalam declare none).
  Tool code is BSD-2-Clause; derived fonts stay OFL 1.1 with the donor's
  OFL.txt kept in fonts/.
- Hand-edits come from the human, reviewed on real hardware; review diffs
  glyph-by-glyph before committing and describe them in the message
  (which letters, what changed, why).

## Commits & releases

- **Conventional Commits are required for PR titles** (enforced by
  `.github/workflows/pr-title.yml`). We squash-merge, so the PR title
  becomes the commit on main — write it as `type: summary`
  (`feat`, `fix`, `docs`, `ci`, `test`, `build`, `chore`, `refactor`,
  `perf`, `style`, `revert`; `type!:` or a `BREAKING CHANGE:` footer for
  breaking).
- **Only `feat:`/`fix:`/breaking bump the version;** everything else just
  lands in the changelog. So a glyph hand-tuning or new-conjunct PR is a
  `feat:`, a rendering bug is a `fix:`, doc/tooling/test PRs are their own
  types and cut no release.
- **Releases are automated by release-please** (`.github/workflows/cd.yaml`).
  It keeps a standing "release PR" that bumps the version and CHANGELOG;
  merging *that* PR tags `vX.Y.Z`. Never bump the version by hand.
- **The version lives in two files, kept in sync by release-please:**
  `pyproject.toml` (via the `python` release-type) and
  `pixelshaper/__init__.py` (via the `# x-release-please-version`
  annotation on the `__version__` line — keep that comment). The seed is
  `.release-please-manifest.json`; pre-1.0 bump flags in
  `release-please-config.json` keep breaking changes inside 0.x.

## Related (not in this repo)

- Living parents: `../manjari-pixel/` (consumes pixelshaper as editable
  path dep), `../nupuram-pixel/` (not yet converted).
- Display consumers: `../led-name-badge-ls32/` (push PNGs via
  `lednamebadge.py -s 4 -m 0 <png>`; needs exactly strip_height-tall
  images), `../malayalam-led-simulator/` (reads the ppem stamp in its
  pixel-scaling mode; re-copy the built TTF + restart its server after
  font changes).

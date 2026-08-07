"""ppem: the sizing landscape for a project, to inform pinning the grid.

Three numbers matter when choosing a ppem, and this report shows all of
them per project:

- **self-scale** per corpus line: the size per-message scaling (the
  simulator's font mode, or font2badge) would pick for that line alone
  (``strip_height x upem / span``). The hardest line's value is the safe
  suggestion; the easiest line's value is what the corpus could enjoy if
  the hard lines didn't exist.
- **glyph ceiling**: the largest size at which every needed glyph still
  fits the strip on its own — above this, single glyphs clip no matter
  how words are placed.
- the **overflow table** in between: for each candidate ppem, how many
  corpus lines exceed the strip and by how much. Pinning above the
  suggestion means paying that overflow down with hand-compression
  (the ManjariPixel treatment: pinned 14 against a suggestion of 10).
"""

import math

from .config import Project
from .donor import Donor


def _shorten(text: str, limit: int = 24) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def report(project: Project, log=print) -> dict:
    donor = Donor(project.donor)
    strip = project.strip_height
    upem = donor.upem

    lines = []
    for text in project.corpus:
        bottom, top = donor.span_units(text)
        span = top - bottom
        if span > 0:
            lines.append((text, span, strip * upem / span))
    if not lines:
        raise ValueError("corpus produced no ink; nothing to report")
    lines.sort(key=lambda item: item[2])

    log(f"donor: {project.donor.name}  upem {upem}  strip {strip} rows")
    log("")
    log("self-scale ppem per corpus line (hardest first):")
    for text, span, pp in lines:
        log(f"  {pp:5.1f}  ({span:5.0f} units)  {_shorten(text)}")

    tall = []
    for gid in sorted(donor.shaped_gids(project.corpus)):
        ext = donor.hb_font.get_glyph_extents(gid)
        height = -ext.height  # HarfBuzz reports height downward
        if height > 0:
            tall.append((height, donor.glyph_name(gid)))
    tall.sort(reverse=True)
    glyph_ceiling = strip * upem / tall[0][0]

    suggestion = donor.suggest_ppem(project.corpus, strip)
    log("")
    log(f"suggestion (every corpus line fits):  {suggestion}")
    log(
        f"glyph ceiling (tallest single glyph): {glyph_ceiling:.1f}"
        f"  ({tall[0][1]}, {tall[0][0]:.0f} units)"
    )
    log("tallest glyphs: " + ", ".join(f"{name} ({h:.0f})" for h, name in tall[:5]))

    hi = math.ceil(lines[-1][2])
    overflow = {}
    log("")
    log("candidate ppem -> corpus lines clipping (worst overflow):")
    for candidate in range(suggestion, hi + 1):
        clipping = [
            (span * candidate / upem - strip, text)
            for text, span, _ in lines
            if span * candidate / upem > strip + 1e-6
        ]
        overflow[candidate] = len(clipping)
        if clipping:
            worst_px, worst_text = max(clipping)
            log(
                f"  {candidate:3d}  {len(clipping)}/{len(lines)} clip"
                f"  (worst +{worst_px:.1f}px: {_shorten(worst_text)})"
            )
        else:
            log(f"  {candidate:3d}  all fit")
        if len(clipping) >= len(lines) - 1:
            break  # only degenerate lines still fit; higher ppems add nothing

    if project.ppem is not None:
        log("")
        clipped = overflow.get(project.ppem)
        if clipped is None:
            clipped = sum(
                1 for _, span, _ in lines if span * project.ppem / upem > strip
            )
        log(f"pinned in pixelshaper.toml: {project.ppem}  ({clipped} lines clip)")

    return {
        "suggestion": suggestion,
        "glyph_ceiling": glyph_ceiling,
        "self_scale": {text: pp for text, _, pp in lines},
        "overflow": overflow,
        "pinned": project.ppem,
    }

"""trace: donor + corpus -> glyphs/<name>.txt text art.

Existing files are SKIPPED by default so hand-edits survive corpus
extensions; --force regenerates everything (destroying hand-edits).
"""

from . import glyphart
from .config import Project
from .donor import Donor


def trace(project: Project, force: bool = False, log=print) -> dict:
    donor = Donor(project.donor)
    ppem = project.ppem
    suggested = donor.suggest_ppem(project.corpus, project.strip_height)
    if ppem is None:
        ppem = suggested
        log(
            f"ppem not pinned; suggesting {ppem} "
            f"(worst corpus string fits {project.strip_height} rows). "
            f"Pin it in pixelshaper.toml to keep the grid stable."
        )
    elif ppem != suggested:
        log(f"ppem pinned at {ppem} (auto-suggest would be {suggested})")

    gids = donor.shaped_gids(project.corpus)
    written, kept = [], []
    for gid in sorted(gids):
        name = donor.glyph_name(gid)
        out = glyphart.path_for(project.glyph_dir, name)
        if out.exists() and not force:
            kept.append(name)
            continue
        gray_rows, advance, left, top = donor.raster(gid, ppem)
        art = glyphart.from_bitmap(
            name, advance, left, top, gray_rows, project.threshold
        )
        glyphart.write(art, project.glyph_dir)
        written.append(name)
        h = len(gray_rows)
        w = len(gray_rows[0]) if gray_rows else 0
        log(f"  {out.name}: {w}x{h} adv={advance}")

    log(
        f"{len(gids)} glyphs needed: {len(written)} traced, "
        f"{len(kept)} kept (hand-edits preserved)"
    )
    return {"ppem": ppem, "needed": len(gids), "written": written, "kept": kept}

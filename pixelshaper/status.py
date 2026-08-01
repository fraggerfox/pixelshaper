"""status: coverage report — corpus needs vs traced vs hand-edited.

"Hand-edited" is detected by re-tracing each needed glyph in memory and
diffing against the file: any difference in art or metrics means a human
(or an older trace) touched it.
"""

from . import glyphart
from .config import Project
from .donor import Donor


def status(project: Project, log=print) -> dict:
    donor = Donor(project.donor)
    ppem = project.ppem or donor.suggest_ppem(project.corpus, project.strip_height)
    needed = {donor.glyph_name(g): g for g in donor.shaped_gids(project.corpus)}
    arts = glyphart.load_dir(project.glyph_dir)
    legacy = glyphart.legacy_files(project.glyph_dir)

    missing = sorted(set(needed) - set(arts))
    extra = sorted(set(arts) - set(needed))
    edited = []
    for name, gid in sorted(needed.items()):
        if name not in arts:
            continue
        gray, adv, left, top = donor.raster(gid, ppem)
        fresh = glyphart.from_bitmap(name, adv, left, top, gray, project.threshold)
        cur = arts[name]
        if ((cur.advance, cur.left, cur.top) != (fresh.advance, fresh.left, fresh.top)
                or [r.rstrip(glyphart.OFF) for r in cur.rows if glyphart.ON in r]
                != [r.rstrip(glyphart.OFF) for r in fresh.rows if glyphart.ON in r]):
            edited.append(name)

    log(f"project: {project.root.name}  donor: {project.donor.name}  "
        f"family: {project.family}  ppem: {ppem}")
    log(f"corpus entries: {len(project.corpus)}  glyphs needed: {len(needed)}")
    log(f"traced: {len(needed) - len(missing)}/{len(needed)}"
        + (f"  MISSING: {', '.join(missing)}" if missing else ""))
    log(f"hand-edited: {len(edited)}")
    for name in edited:
        log(f"  ~ {name}")
    if extra:
        log(f"not needed by current corpus ({len(extra)}): {', '.join(extra)}")
    if legacy:
        log(f"gid-keyed legacy files: {len(legacy)} — run `pixelshaper migrate`")
    return {"needed": sorted(needed), "missing": missing,
            "edited": edited, "extra": extra, "legacy": len(legacy)}


def migrate(project: Project, log=print) -> dict:
    """Rename gid-keyed NNNN_name.txt files to name-keyed, dropping the
    gid header field. Hand-edits are preserved byte-for-byte in the art."""
    moved, skipped = [], []
    for old in glyphart.legacy_files(project.glyph_dir):
        art = glyphart.parse(old)  # tolerates the extra gid: header line
        new = glyphart.path_for(project.glyph_dir, art.name)
        if new.exists() and new != old:
            skipped.append((old.name, new.name))
            log(f"  SKIP {old.name}: {new.name} already exists")
            continue
        glyphart.write(art, project.glyph_dir)
        if new != old:
            old.unlink()
        moved.append((old.name, new.name))
        log(f"  {old.name} -> {new.name}")
    log(f"migrated {len(moved)} files, {len(skipped)} skipped")
    return {"moved": moved, "skipped": skipped}

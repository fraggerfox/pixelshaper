"""build: glyphs/*.txt -> build/<Family>.ttf.

Takes the donor for cmap/GSUB/GPOS, replaces the outlines of every glyph
present in glyphs/ with axis-aligned squares on a grid of
1 px = upem/ppem font units, quantizes advances and GPOS positioning to
that grid, renames the family, and stamps the native ppem into the
unique-ID name record. Rendering at exactly `ppem` px reproduces the
text-art dot for dot.
"""

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

from . import glyphart
from .config import Project
from .donor import Donor

_POS_ATTRS = ("XCoordinate", "YCoordinate", "XPlacement",
              "YPlacement", "XAdvance", "YAdvance")


def _rects(art: glyphart.GlyphArt):
    """Merge horizontal runs of on-pixels into rectangles (px, y up)."""
    for r, row in enumerate(art.rows):
        y1 = art.top - r          # top edge of this pixel row
        c = 0
        while c < len(row):
            if row[c] == glyphart.ON:
                c0 = c
                while c < len(row) and row[c] == glyphart.ON:
                    c += 1
                yield (art.left + c0, y1 - 1, art.left + c, y1)
            else:
                c += 1


def _quantize_gpos(table, units_per_px: float):
    seen = set()

    def q(v):
        return int(round(v / units_per_px) * units_per_px) if v else v

    def walk(obj):
        if id(obj) in seen or obj is None:
            return
        seen.add(id(obj))
        if isinstance(obj, (list, tuple)):
            for item in obj:
                walk(item)
            return
        if not hasattr(obj, "__dict__"):
            return
        for attr, val in vars(obj).items():
            if attr in _POS_ATTRS and isinstance(val, int):
                setattr(obj, attr, q(val))
            else:
                walk(val)

    walk(table.table)


def build(project: Project, log=print) -> dict:
    if project.ppem is None:
        raise ValueError("pin [output] ppem in pixelshaper.toml before building")
    donor = Donor(project.donor)
    font = TTFont(str(project.donor))
    units_per_px = font["head"].unitsPerEm / project.ppem

    def px(n):
        return int(round(n * units_per_px))

    arts = glyphart.load_dir(project.glyph_dir)
    if not arts:
        raise FileNotFoundError(f"no glyph files in {project.glyph_dir}; run trace first")
    legacy = glyphart.legacy_files(project.glyph_dir)
    if legacy:
        raise ValueError(
            f"{len(legacy)} gid-keyed glyph files (e.g. {legacy[0].name}) in "
            f"{project.glyph_dir}; run `pixelshaper migrate` first")

    glyf, hmtx = font["glyf"], font["hmtx"]
    glyph_set = font.getGlyphSet()
    known = set(font.getGlyphOrder())
    for name, art in arts.items():
        if name not in known:
            raise KeyError(f"glyph {name!r} ({glyphart.path_for(project.glyph_dir, name).name}) "
                           f"not in donor {project.donor.name}")
        pen = TTGlyphPen(glyph_set)
        for x0, y0, x1, y1 in _rects(art):
            pen.moveTo((px(x0), px(y0)))
            pen.lineTo((px(x1), px(y0)))
            pen.lineTo((px(x1), px(y1)))
            pen.lineTo((px(x0), px(y1)))
            pen.closePath()
        glyf[name] = pen.glyph()
        hmtx[name] = (px(art.advance), px(art.left))

    if "GPOS" in font:
        _quantize_gpos(font["GPOS"], units_per_px)

    family = project.family
    stamp = f"{family}-{project.ppem}px;derived-from-{donor.family_name}"
    name_tbl = font["name"]
    for nid, val in ((1, family), (3, stamp), (4, f"{family} Regular"),
                     (6, f"{family}-Regular"), (16, family)):
        name_tbl.setName(val, nid, 3, 1, 0x409)

    project.build_dir.mkdir(exist_ok=True)
    font.save(str(project.ttf_path))
    log(f"{len(arts)} glyphs pixelized at {project.ppem}ppem "
        f"(1px = {units_per_px:.1f} units) -> {project.ttf_path}")
    return {"glyphs": len(arts), "ttf": project.ttf_path, "stamp": stamp}

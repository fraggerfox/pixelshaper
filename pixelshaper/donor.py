"""Donor font access: fontTools (names/tables), FreeType (raster),
HarfBuzz (shaping). One consistent naming source: fontTools glyph order."""

import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from pathlib import Path


class Donor:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self.tt = TTFont(str(self.path))
        self.glyph_order = self.tt.getGlyphOrder()
        blob = hb.Blob.from_file_path(str(self.path))
        self.hb_face = hb.Face(blob)
        self.hb_font = hb.Font(self.hb_face)
        self.upem = self.hb_face.upem
        self.ft = freetype.Face(str(self.path))
        if "glyf" not in self.tt:
            raise NotImplementedError(
                f"{self.path.name}: CFF/OTF donors are a T2 work item; "
                "convert to TrueType outlines first (e.g. with fontmake)"
            )

    def glyph_name(self, gid: int) -> str:
        return self.glyph_order[gid]

    @property
    def family_name(self) -> str:
        return self.tt["name"].getDebugName(1) or self.path.stem

    def shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf)
        return buf

    def shaped_gids(self, texts) -> set[int]:
        gids: set[int] = set()
        for text in texts:
            gids |= {info.codepoint for info in self.shape(text).glyph_infos}
        return gids

    def span_units(self, text: str) -> tuple[float, float]:
        """(bottom, top) ink extent of the shaped text in font units (y up)."""
        bottom, top = 1e9, -1e9
        buf = self.shape(text)
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            ext = self.hb_font.get_glyph_extents(info.codepoint)
            if ext.width == 0 and ext.height == 0:
                continue
            t = pos.y_offset + ext.y_bearing
            top = max(top, t)
            bottom = min(bottom, t + ext.height)
        return bottom, top

    def suggest_ppem(self, corpus, strip_height: int) -> int:
        """Largest integer ppem at which every corpus string fits the strip
        on its own baseline (per-string span, not the union of extremes)."""
        max_span = 0.0
        for text in corpus:
            bottom, top = self.span_units(text)
            max_span = max(max_span, top - bottom)
        if max_span <= 0:
            raise ValueError("corpus produced no ink; cannot suggest ppem")
        return max(1, int(strip_height * self.upem // max_span))

    def raster(self, gid: int, ppem: int):
        """Grayscale raster of one glyph: (gray_rows, advance_px, left, top)."""
        self.ft.set_char_size(ppem * 64)
        self.ft.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = self.ft.glyph
        bm = g.bitmap
        buf = bytes(bm.buffer)  # fetch once: the property is O(n) per access
        gray_rows = [
            list(buf[r * bm.pitch : r * bm.pitch + bm.width]) for r in range(bm.rows)
        ]
        return gray_rows, round(g.advance.x / 64), g.bitmap_left, g.bitmap_top

"""render: text -> terminal grid + badge-ready PNG, at the native ppem.

1-bit mono — a correct pixel font needs no grayscale/threshold tricks.
Default placement gives each whitespace token its own baseline (a word
with high marks and one with deep tails each get the full strip);
shared=True locks the whole string to one baseline (alphabet strips,
where per-word centring would look wavy).
"""

import hashlib
from pathlib import Path

import freetype
import numpy as np
import uharfbuzz as hb
from PIL import Image

from . import glyphart
from .config import Project


class _PixelFont:
    def __init__(self, project: Project):
        if not project.ttf_path.is_file():
            raise FileNotFoundError(f"{project.ttf_path}; run build first")
        if project.ppem is None:
            raise ValueError("pin [output] ppem in pixelshaper.toml")
        self.ppem = project.ppem
        self.strip_h = project.strip_height
        blob = hb.Blob.from_file_path(str(project.ttf_path))
        self.hb_font = hb.Font(hb.Face(blob))
        self.hb_font.scale = (self.ppem * 64,) * 2
        self.ft = freetype.Face(str(project.ttf_path))
        self.ft.set_char_size(self.ppem * 64)

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf)
        return buf


def _unpack_mono(bm):
    packed = np.frombuffer(bytes(bm.buffer), dtype=np.uint8).reshape(bm.rows, bm.pitch)
    return np.unpackbits(packed, axis=1)[:, : bm.width].astype(bool)


def _render_run(pf: _PixelFont, text: str, log=print):
    H = pf.strip_h
    buf = pf.shape(text)
    top, bottom = -1e9, 1e9
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ext = pf.hb_font.get_glyph_extents(info.codepoint)
        if ext.width == 0 and ext.height == 0:
            continue
        t = (pos.y_offset + ext.y_bearing) / 64
        top = max(top, t)
        bottom = min(bottom, t + ext.height / 64)
    if top < bottom:  # no ink
        return np.zeros((H, 1), bool)
    top_px = int(round(top))
    span = top - bottom
    if span > H:
        log(f"WARNING: ink span {span:.1f}px exceeds {H} rows; clipping — {text!r}")
    else:
        top_px += (H - int(round(span))) // 2  # centre short tokens

    width = int(pf.ppem * max(1, len(text)) * 1.5) + 20
    panel = np.zeros((H, width), bool)
    pen_x = 2.0
    flags = (
        freetype.FT_LOAD_RENDER
        | freetype.FT_LOAD_TARGET_MONO
        | freetype.FT_LOAD_NO_HINTING
    )
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pf.ft.load_glyph(info.codepoint, flags)
        bm = pf.ft.glyph.bitmap
        if bm.width and bm.rows:
            bits = _unpack_mono(bm)
            x = int(round(pen_x + pos.x_offset / 64 + pf.ft.glyph.bitmap_left))
            y = int(round(top_px - (pos.y_offset / 64 + pf.ft.glyph.bitmap_top)))
            r0, c0 = max(y, 0), max(x, 0)
            r1 = min(y + bits.shape[0], H)
            c1 = min(x + bits.shape[1], width)
            if r1 > r0 and c1 > c0:
                panel[r0:r1, c0:c1] |= bits[r0 - y : r1 - y, c0 - x : c1 - x]
        pen_x += pos.x_advance / 64
    inked = np.where(panel.any(axis=0))[0]
    return panel[:, : inked.max() + 2] if len(inked) else panel[:, :1]


def render_text(
    project: Project, text: str, gap: int = 3, shared: bool = False, log=print
) -> np.ndarray:
    pf = _PixelFont(project)
    if shared:
        return _render_run(pf, text, log)
    panels = []
    for word in text.split():
        panels.append(_render_run(pf, word, log))
        panels.append(np.zeros((pf.strip_h, gap), bool))
    return np.hstack(panels[:-1]) if panels else np.zeros((pf.strip_h, 1), bool)


def save_png(project: Project, bits: np.ndarray, text: str) -> Path:
    project.build_dir.mkdir(exist_ok=True)
    digest = hashlib.md5(text.encode()).hexdigest()[:8]
    out = project.build_dir / f"{project.family.lower()}-{digest}.png"
    Image.fromarray(np.where(bits, 255, 0).astype(np.uint8), mode="L").save(out)
    return out


def render_cli(project: Project, texts, gap=3, shared=False, log=print):
    results = []
    for text in texts:
        bits = render_text(project, text, gap=gap, shared=shared, log=log)
        out = save_png(project, bits, text)
        log(f"\n=== {text}  ({bits.shape[1]}x{bits.shape[0]})  -> {out.name} ===")
        for row in bits:
            log("".join(glyphart.ON if p else glyphart.OFF for p in row))
        results.append(out)
    return results

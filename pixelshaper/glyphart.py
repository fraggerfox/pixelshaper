"""The text-art glyph format: one file per glyph, ●/· grid + metrics header.

Files are keyed by GLYPH NAME (not gid): donor updates may renumber glyph
indices, but names are stable, so hand-edits survive. The filename is a
sanitized form of the name; the authoritative name lives in the header.
"""

import re
from dataclasses import dataclass
from pathlib import Path

ON, OFF = "●", "·"
_HEADER_RE = re.compile(r"^(\w+):\s*(.*)$")


@dataclass
class GlyphArt:
    name: str
    advance: int  # pen advance, px
    left: int  # left side bearing, px
    top: int  # top edge of the grid relative to baseline, px
    rows: list[str]  # ●/· strings; may include leading/trailing blanks

    @property
    def bits(self) -> list[list[bool]]:
        return [[ch == ON for ch in row] for row in self.rows]

    @property
    def ink_span(self) -> tuple[int, int] | None:
        """(top, bottom) of actual ink in baseline-relative px, or None."""
        inked = [i for i, row in enumerate(self.rows) if ON in row]
        if not inked:
            return None
        return self.top - inked[0], self.top - inked[-1] - 1


def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "_"


def path_for(glyph_dir: Path, name: str) -> Path:
    return glyph_dir / f"{sanitize(name)}.txt"


def parse(path: Path) -> GlyphArt:
    head: dict[str, str] = {}
    rows: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not rows and (m := _HEADER_RE.match(line)):
            head[m.group(1)] = m.group(2).strip()
        elif line.strip():
            rows.append(line)
    missing = {"name", "advance", "left", "top"} - head.keys()
    if missing:
        raise ValueError(f"{path}: missing header fields {sorted(missing)}")
    return GlyphArt(
        name=head["name"],
        advance=int(head["advance"]),
        left=int(head["left"]),
        top=int(head["top"]),
        rows=rows,
    )


def write(art: GlyphArt, glyph_dir: Path) -> Path:
    glyph_dir.mkdir(exist_ok=True)
    out = path_for(glyph_dir, art.name)
    header = [
        f"name: {art.name}",
        f"advance: {art.advance}",
        f"left: {art.left}",
        f"top: {art.top}",
    ]
    out.write_text("\n".join(header + [""] + art.rows) + "\n", encoding="utf-8")
    return out


def from_bitmap(name, advance, left, top, gray_rows, threshold_frac) -> GlyphArt:
    """Build art from a grayscale raster (list of byte rows), thresholded
    at threshold_frac of the glyph's own peak coverage."""
    peak = max((max(r) for r in gray_rows if r), default=0)
    cut = max(int(peak * threshold_frac), 1)
    rows = ["".join(ON if v >= cut else OFF for v in r) for r in gray_rows]
    return GlyphArt(name=name, advance=advance, left=left, top=top, rows=rows)


def load_dir(glyph_dir: Path) -> dict[str, GlyphArt]:
    """All parseable glyph files, keyed by glyph name."""
    arts: dict[str, GlyphArt] = {}
    if not glyph_dir.is_dir():
        return arts
    for p in sorted(glyph_dir.glob("*.txt")):
        art = parse(p)
        arts[art.name] = art
    return arts

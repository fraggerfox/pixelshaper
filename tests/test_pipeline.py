"""End-to-end pipeline tests on a throwaway one-letter project."""

import numpy as np
from fontTools.ttLib import TTFont

from pixelshaper import glyphart
from pixelshaper.build import build
from pixelshaper.render import render_text
from pixelshaper.trace import trace

quiet = lambda *a, **k: None  # noqa: E731


def _ink_bbox(bits: np.ndarray) -> np.ndarray:
    rows = np.where(bits.any(axis=1))[0]
    cols = np.where(bits.any(axis=0))[0]
    return bits[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]


def test_trace_skips_existing_and_force_overwrites(mini_project):
    trace(mini_project, log=quiet)
    path = glyphart.path_for(mini_project.glyph_dir, "k1")
    assert path.exists()

    # simulate a hand-edit, retrace: the edit must survive
    edited = path.read_text().replace("●", "·", 1)
    path.write_text(edited)
    trace(mini_project, log=quiet)
    assert path.read_text() == edited

    # --force regenerates
    trace(mini_project, force=True, log=quiet)
    assert path.read_text() != edited


def test_build_stamps_and_renames(mini_project):
    trace(mini_project, log=quiet)
    result = build(mini_project, log=quiet)
    assert mini_project.ttf_path.exists()
    assert result["stamp"] == "TestPixel-14px;derived-from-Manjari"
    name = TTFont(str(mini_project.ttf_path))["name"]
    assert name.getDebugName(1) == "TestPixel"
    assert "TestPixel-14px" in name.getDebugName(3)


def test_render_reproduces_glyph_art_pixel_for_pixel(mini_project):
    """The core invariant: text art -> TTF -> HarfBuzz+FreeType 1-bit render
    must reproduce the art exactly (modulo placement padding)."""
    trace(mini_project, log=quiet)
    build(mini_project, log=quiet)
    art = glyphart.parse(glyphart.path_for(mini_project.glyph_dir, "k1"))
    rendered = render_text(mini_project, "ക", log=quiet)
    assert np.array_equal(_ink_bbox(rendered), _ink_bbox(np.array(art.bits)))


def test_hand_edit_shows_up_in_render(mini_project):
    """Flipping one pixel in the art must change the render accordingly."""
    trace(mini_project, log=quiet)
    build(mini_project, log=quiet)
    before = _ink_bbox(render_text(mini_project, "ക", log=quiet))

    path = glyphart.path_for(mini_project.glyph_dir, "k1")
    art = glyphart.parse(path)
    top_ink = next(i for i, r in enumerate(art.rows) if glyphart.ON in r)
    art.rows[top_ink] = art.rows[top_ink].replace(glyphart.ON, glyphart.OFF, 1)
    glyphart.write(art, mini_project.glyph_dir)
    build(mini_project, log=quiet)
    after = _ink_bbox(render_text(mini_project, "ക", log=quiet))

    assert not np.array_equal(before, after)
    assert int(before.sum()) - int(after.sum()) == 1  # exactly one pixel gone

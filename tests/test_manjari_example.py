"""Real-world tests against examples/manjari-pixel: a committed project
with both auto-traced and heavily hand-edited glyphs."""

import numpy as np

from pixelshaper import config
from pixelshaper.build import build
from pixelshaper.render import render_text
from pixelshaper.status import status

quiet = lambda *a, **k: None  # noqa: E731


def test_status_full_coverage_and_hand_edits(manjari_example):
    report = status(config.load(manjari_example), log=quiet)
    assert report["missing"] == []
    # the project carries substantial hand-tuning; z1z1 (ശ്ശ) was the most
    # reworked glyph of all — if these ever read as untouched, detection broke
    assert len(report["edited"]) > 20
    assert "z1z1" in report["edited"]


def test_full_corpus_renders_without_clipping(manjari_example, tmp_path):
    project = config.load(manjari_example)
    build(project, log=quiet)
    warnings = []
    for line in project.corpus:
        bits = render_text(project, line, gap=8, log=warnings.append)
        assert bits.shape[0] == project.strip_height
        assert bits.any(), f"no ink for {line!r}"
    assert warnings == [], f"clipping: {warnings}"


def test_render_is_deterministic(manjari_example):
    project = config.load(manjari_example)
    build(project, log=quiet)
    a = render_text(project, "മലയാളം", log=quiet)
    b = render_text(project, "മലയാളം", log=quiet)
    assert np.array_equal(a, b)

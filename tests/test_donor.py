"""Donor tests against the real committed Manjari donor."""

from pixelshaper import config
from pixelshaper.donor import Donor


def test_basic_facts(manjari_example):
    d = Donor(manjari_example / "fonts" / "Manjari-Regular.ttf")
    assert d.upem == 2048
    assert d.family_name == "Manjari"


def test_shaping_discovers_conjunct_ligature(manjari_example):
    d = Donor(manjari_example / "fonts" / "Manjari-Regular.ttf")
    names = {d.glyph_name(g) for g in d.shaped_gids(["ക്ക"])}
    # ക്ക must shape to the k1k1 ligature glyph — reachable only via GSUB
    assert "k1k1" in names


def test_span_and_ppem_suggestion(manjari_example):
    d = Donor(manjari_example / "fonts" / "Manjari-Regular.ttf")
    bottom, top = d.span_units("മലയാളം")
    assert top > 0 > bottom  # ink above and below the baseline
    project = config.load(manjari_example)
    # The example pins 14, but the corpus-driven suggestion (worst line is
    # the സ്ത്രീ strip) is 10 — the pin is a deliberate override.
    assert d.suggest_ppem(project.corpus, project.strip_height) == 10


def test_raster_returns_pixel_metrics(manjari_example):
    d = Donor(manjari_example / "fonts" / "Manjari-Regular.ttf")
    (gid,) = d.shaped_gids(["ക"]) - d.shaped_gids([" "])
    gray, advance, left, top = d.raster(gid, 14)
    assert gray and any(any(v > 0 for v in row) for row in gray)
    assert advance > 0
    assert top > 0

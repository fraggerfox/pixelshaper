"""ppem report: self-scale values, glyph ceiling, overflow accounting."""

from pixelshaper import cli, config
from pixelshaper.ppem import report


def quiet(*a, **k):
    pass


def test_report_shape_on_mini_project(mini_project):
    out = report(mini_project, log=quiet)
    # single-letter corpus: one self-scale entry
    assert list(out["self_scale"]) == ["ക"]
    # suggestion never exceeds any line's self-scale or the glyph ceiling
    assert out["suggestion"] <= out["self_scale"]["ക"]
    assert out["suggestion"] <= out["glyph_ceiling"]
    # at the suggestion itself nothing clips
    assert out["overflow"][out["suggestion"]] == 0
    assert out["pinned"] == mini_project.ppem


def test_report_on_manjari_example(manjari_example):
    project = config.load(manjari_example)
    out = report(project, log=quiet)
    # the known landscape: suggestion 10, pinned 14 with overflow to repay
    assert out["suggestion"] == 10
    assert out["pinned"] == 14
    assert out["overflow"][14] > 0
    # every corpus line self-scales at or above the suggestion
    for value in out["self_scale"].values():
        assert value >= out["suggestion"]


def test_cli_ppem_subcommand(manjari_example, capsys):
    assert cli.main(["-C", str(manjari_example), "ppem"]) == 0
    out = capsys.readouterr().out
    assert "self-scale ppem per corpus line" in out
    assert "glyph ceiling" in out
    assert "pinned in pixelshaper.toml: 14" in out

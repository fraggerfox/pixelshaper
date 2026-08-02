"""In-process CLI tests: dispatch, exit codes, and printed output."""

import pytest

from pixelshaper import cli


def test_version_exits_zero():
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0


def test_missing_config_exit_2(tmp_path, capsys):
    assert cli.main(["-C", str(tmp_path), "status"]) == 2
    assert "pixelshaper.toml" in capsys.readouterr().err


def test_command_failure_exit_1(mini_project, capsys):
    # build before trace: no glyph files -> library error -> exit 1
    assert cli.main(["-C", str(mini_project.root), "build"]) == 1
    assert "run trace first" in capsys.readouterr().err


def test_full_flow_through_cli(mini_project, capsys):
    root = str(mini_project.root)
    assert cli.main(["-C", root, "trace"]) == 0
    assert cli.main(["-C", root, "build"]) == 0
    assert cli.main(["-C", root, "render", "ക"]) == 0
    out = capsys.readouterr().out
    assert "===" in out and "testpixel-" in out
    assert cli.main(["-C", root, "status"]) == 0
    assert "hand-edited: 0" in capsys.readouterr().out

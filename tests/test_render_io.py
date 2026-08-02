"""Render I/O surfaces: PNG saving, shared mode, guards, clipping warning."""

import hashlib

import pytest
from PIL import Image

from pixelshaper import config
from pixelshaper.build import build
from pixelshaper.render import render_cli, render_text
from pixelshaper.trace import trace

quiet = lambda *a, **k: None  # noqa: E731


def _prepared(project):
    trace(project, log=quiet)
    build(project, log=quiet)
    return project


def test_render_before_build_raises(mini_project):
    trace(mini_project, log=quiet)
    with pytest.raises(FileNotFoundError, match="run build first"):
        render_text(mini_project, "ക", log=quiet)


def test_render_cli_writes_documented_png(mini_project):
    project = _prepared(mini_project)
    (out,) = render_cli(project, ["ക"], log=quiet)
    digest = hashlib.md5("ക".encode()).hexdigest()[:8]
    assert out.name == f"testpixel-{digest}.png"
    img = Image.open(out)
    assert img.height == project.strip_height
    assert img.mode == "L"


def test_shared_baseline_mode(mini_project):
    project = _prepared(mini_project)
    bits = render_text(project, "ക ക", shared=True, log=quiet)
    assert bits.shape[0] == project.strip_height
    assert bits.any()


def test_whitespace_only_renders_blank(mini_project):
    project = _prepared(mini_project)
    bits = render_text(project, "  ", shared=True, log=quiet)
    assert not bits.any()


def test_clipping_warning_fires_when_ppem_exceeds_strip(mini_project):
    # Rebuild the same project at a deliberately oversized ppem: the letter
    # is now taller than the strip and the render must say so.
    toml = mini_project.root / "pixelshaper.toml"
    toml.write_text(toml.read_text().replace("ppem = 14", "ppem = 30"))
    project = config.load(mini_project.root)
    trace(project, force=True, log=quiet)
    build(project, log=quiet)
    messages = []
    render_text(project, "ക", log=messages.append)
    assert any("clipping" in m for m in messages)

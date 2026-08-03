import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MANJARI_EXAMPLE = REPO / "examples" / "manjari-pixel"
MANJARI_DONOR = MANJARI_EXAMPLE / "fonts" / "Manjari-Regular.ttf"


@pytest.fixture(scope="session")
def manjari_example():
    """The real-world project: committed donor, traced + hand-edited glyphs."""
    return MANJARI_EXAMPLE


@pytest.fixture()
def mini_project(tmp_path):
    """A tiny throwaway project using the Manjari donor, corpus = one letter."""
    (tmp_path / "fonts").mkdir()
    shutil.copy(MANJARI_DONOR, tmp_path / "fonts" / "Manjari-Regular.ttf")
    (tmp_path / "pixelshaper.toml").write_text(
        '[donor]\nfile = "fonts/Manjari-Regular.ttf"\n\n'
        '[output]\nfamily = "TestPixel"\nppem = 14\nthreshold = 0.35\n\n'
        "[display]\nstrip_height = 11\n",
        encoding="utf-8",
    )
    (tmp_path / "corpus.txt").write_text("ക\n", encoding="utf-8")
    from pixelshaper import config

    return config.load(tmp_path)

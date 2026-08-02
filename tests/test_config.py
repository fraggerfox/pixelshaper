import pytest

from pixelshaper import config


def _write(tmp_path, toml, corpus=None):
    (tmp_path / "pixelshaper.toml").write_text(toml)
    if corpus is not None:
        (tmp_path / "corpus.txt").write_text(corpus)
    return tmp_path


BASE = '[donor]\nfile = "fonts/X.ttf"\n\n[output]\nfamily = "XPixel"\n'


def test_load_minimal_defaults(tmp_path):
    p = config.load(_write(tmp_path, BASE))
    assert p.family == "XPixel"
    assert p.ppem is None
    assert p.threshold == 0.5
    assert p.strip_height == 11
    assert p.corpus == []
    assert p.ttf_path == tmp_path / "build" / "XPixel.ttf"


def test_corpus_skips_comments_and_blanks(tmp_path):
    p = config.load(_write(tmp_path, BASE, "# c\n\nമലയാളം\n  കേരളം  \n"))
    assert p.corpus == ["മലയാളം", "കേരളം"]


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        config.load(tmp_path)


def test_missing_family_raises(tmp_path):
    with pytest.raises(ValueError, match="family"):
        config.load(_write(tmp_path, '[donor]\nfile = "f.ttf"\n'))


def test_variable_font_instance_not_implemented(tmp_path):
    toml = BASE.replace(
        'file = "fonts/X.ttf"', 'file = "fonts/X.ttf"\ninstance = { wght = 400 }'
    )
    with pytest.raises(NotImplementedError):
        config.load(_write(tmp_path, toml))

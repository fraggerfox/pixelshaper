from pixelshaper import glyphart


def test_write_parse_roundtrip(tmp_path):
    art = glyphart.GlyphArt(
        name="ml_lla", advance=10, left=-2, top=7, rows=["·●·", "●·●", "·●·"]
    )
    path = glyphart.write(art, tmp_path)
    assert path.name == "ml_lla.txt"
    back = glyphart.parse(path)
    assert back == art


def test_filename_sanitized_but_name_authoritative(tmp_path):
    art = glyphart.GlyphArt(name="k1th1.alt слон", advance=1, left=0, top=1, rows=["●"])
    path = glyphart.write(art, tmp_path)
    assert "/" not in path.stem and " " not in path.name
    assert glyphart.parse(path).name == "k1th1.alt слон"


def test_parse_missing_header_field(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("name: x\nadvance: 3\n\n●●\n", encoding="utf-8")  # no left/top
    try:
        glyphart.parse(p)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "left" in str(e) and "top" in str(e)


def test_from_bitmap_threshold_is_fraction_of_peak():
    gray = [[0, 200], [90, 10]]
    art = glyphart.from_bitmap("g", 2, 0, 2, gray, 0.5)  # cut at 100
    assert art.rows == ["·●", "··"]
    art = glyphart.from_bitmap("g", 2, 0, 2, gray, 0.4)  # cut at 80
    assert art.rows == ["·●", "●·"]


def test_ink_span_ignores_blank_rows():
    art = glyphart.GlyphArt(
        name="g", advance=3, left=0, top=8, rows=["···", "●●·", "···", "·●·", "···"]
    )
    # ink rows are indices 1 and 3: top edge 8-1=7, bottom edge 8-3-1=4
    assert art.ink_span == (7, 4)
    blank = glyphart.GlyphArt(name="sp", advance=2, left=0, top=0, rows=[])
    assert blank.ink_span is None


def test_spaced_and_compact_files_parse_identically(tmp_path):
    header = "name: x\nadvance: 3\nleft: 0\ntop: 2\n\n"
    compact = tmp_path / "compact.txt"
    spaced = tmp_path / "spaced.txt"
    compact.write_text(header + "●·●\n·●·\n", encoding="utf-8")
    spaced.write_text(header + "● · ●\n· ● ·\n", encoding="utf-8")
    a, b = glyphart.parse(compact), glyphart.parse(spaced)
    assert a.rows == b.rows == ["●·●", "·●·"]


def test_write_emits_spaced_and_round_trips(tmp_path):
    art = glyphart.GlyphArt(name="x", advance=3, left=0, top=2, rows=["●·●", "·●·"])
    p = glyphart.write(art, tmp_path)
    text = p.read_text(encoding="utf-8")
    assert "● · ●" in text  # visually square on disk
    assert glyphart.parse(p) == art  # compact in memory

"""Project configuration: pixelshaper.toml + corpus.txt."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "pixelshaper.toml"
CORPUS_NAME = "corpus.txt"


@dataclass
class Project:
    root: Path
    donor: Path
    family: str
    ppem: int | None  # None -> auto-suggest at trace time
    threshold: float
    strip_height: int
    corpus: list[str] = field(default_factory=list)
    instance: dict | None = None  # variable-font axis pins (T2)

    @property
    def glyph_dir(self) -> Path:
        return self.root / "glyphs"

    @property
    def build_dir(self) -> Path:
        return self.root / "build"

    @property
    def ttf_path(self) -> Path:
        return self.build_dir / f"{self.family}.ttf"


def load(root: Path | str) -> Project:
    root = Path(root).resolve()
    config_path = root / CONFIG_NAME
    if not config_path.is_file():
        raise FileNotFoundError(f"no {CONFIG_NAME} in {root}")
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))

    donor_tbl = raw.get("donor", {})
    output = raw.get("output", {})
    display = raw.get("display", {})
    if "file" not in donor_tbl:
        raise ValueError(f"{CONFIG_NAME}: [donor] file is required")
    if "family" not in output:
        raise ValueError(f"{CONFIG_NAME}: [output] family is required")

    corpus_path = root / CORPUS_NAME
    corpus = []
    if corpus_path.is_file():
        for line in corpus_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                corpus.append(line)

    instance = donor_tbl.get("instance")
    if instance:
        raise NotImplementedError(
            "[donor] instance (variable-font pinning) is a T2 work item; "
            "instantiate the donor with fontTools varLib.instancer for now"
        )

    return Project(
        root=root,
        donor=root / donor_tbl["file"],
        family=output["family"],
        ppem=output.get("ppem"),
        threshold=float(output.get("threshold", 0.5)),
        strip_height=int(display.get("strip_height", 11)),
        corpus=corpus,
        instance=instance,
    )

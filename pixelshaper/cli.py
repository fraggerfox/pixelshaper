"""pixelshaper CLI — thin wrapper over the library modules."""

import argparse
import sys

from . import __version__, config
from .build import build
from .render import render_cli
from .status import status
from .trace import trace


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="pixelshaper",
        description="Shaping-aware pixel fonts from OpenType donors",
    )
    ap.add_argument("--version", action="version", version=f"pixelshaper {__version__}")
    ap.add_argument("-C", "--project", default=".", metavar="DIR",
                    help="project directory containing pixelshaper.toml (default: .)")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("trace", help="donor + corpus -> glyphs/<name>.txt")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing glyph files (DESTROYS hand-edits)")

    sub.add_parser("build", help="glyphs/ -> build/<Family>.ttf")

    p = sub.add_parser("render", help="render text at the native ppem")
    p.add_argument("texts", nargs="*", help="texts to render (default: the corpus)")
    p.add_argument("--gap", type=int, default=3,
                   help="blank columns between words (default 3)")
    p.add_argument("--shared", action="store_true",
                   help="one shared baseline for the whole string")

    sub.add_parser("status", help="coverage report: needed/traced/hand-edited")

    args = ap.parse_args(argv)
    try:
        project = config.load(args.project)
    except (FileNotFoundError, ValueError) as e:
        print(f"pixelshaper: {e}", file=sys.stderr)
        return 2

    try:
        if args.command == "trace":
            trace(project, force=args.force)
        elif args.command == "build":
            build(project)
        elif args.command == "render":
            render_cli(project, args.texts or project.corpus,
                       gap=args.gap, shared=args.shared)
        elif args.command == "status":
            status(project)
    except (FileNotFoundError, ValueError, KeyError, NotImplementedError) as e:
        print(f"pixelshaper {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

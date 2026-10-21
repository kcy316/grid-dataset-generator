"""Command line interface: `python -m gridgen {generate,split,run}`."""

from __future__ import annotations

import argparse
from pathlib import Path

from gridgen.config import Settings, load_settings
from gridgen.generate import generate_subject
from gridgen.split import split_all


def _read_subjects(args) -> list[tuple[str, int]]:
    """Collect (subject, batches) pairs from --subject flags and/or a subjects file."""
    subjects = [(s, args.batches) for s in (args.subject or [])]
    if args.subjects_file:
        for line in Path(args.subjects_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Optional "| N" suffix sets the batch count for that line.
            text, _, count = line.partition("|")
            subjects.append((text.strip(), int(count) if count.strip() else args.batches))
    if not subjects:
        raise SystemExit("error: give at least one --subject or a --subjects-file")
    return subjects


def _settings_from_args(args) -> Settings:
    return load_settings().with_overrides(
        rows=args.rows,
        cols=args.cols,
        tile_size=getattr(args, "tile_size", None),
        inner_crop=getattr(args, "inner_crop", None),
        image_quality=getattr(args, "quality", None),
        output_dir=Path(args.output) if args.output else None,
        overwrite=True if args.overwrite else None,
        use_llm_variation=False if getattr(args, "no_llm_variation", False) else None,
    )


def cmd_generate(args) -> None:
    settings = _settings_from_args(args)
    for subject, batches in _read_subjects(args):
        generate_subject(settings, subject, batches, dry_run=args.dry_run)


def cmd_split(args) -> None:
    s = _settings_from_args(args)
    split_all(s.grid_dir, s.tile_dir, s.rows, s.cols, s.tile_size, s.inner_crop, s.overwrite,
              pattern=args.pattern)


def cmd_run(args) -> None:
    cmd_generate(args)
    if not args.dry_run:
        cmd_split(args)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--rows", type=int, help="grid rows (default: GRID_ROWS or 4)")
    common.add_argument("--cols", type=int, help="grid columns (default: GRID_COLS or 4)")
    common.add_argument("--output", help="output directory (default: ./output)")
    common.add_argument("--overwrite", action="store_true", help="overwrite existing files")

    gen = argparse.ArgumentParser(add_help=False)
    gen.add_argument("--subject", action="append", help="what to photograph; repeatable")
    gen.add_argument("--subjects-file", help="text file, one subject per line ('subject | batches')")
    gen.add_argument("--batches", type=int, default=1, help="grids per subject (default: 1)")
    gen.add_argument("--quality", choices=["low", "medium", "high", "auto"])
    gen.add_argument("--no-llm-variation", action="store_true",
                     help="use built-in style presets instead of a text model (cheaper)")
    gen.add_argument("--dry-run", action="store_true", help="print prompts, call no API")

    spl = argparse.ArgumentParser(add_help=False)
    spl.add_argument("--tile-size", type=int, help="output tile size in px (default: 640)")
    spl.add_argument("--inner-crop", type=float, help="fraction trimmed from each cell edge (0-0.4)")
    spl.add_argument("--pattern", default="*.png", help="glob for grid files (default: *.png)")

    parser = argparse.ArgumentParser(prog="gridgen", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate", parents=[common, gen], help="generate grid images").set_defaults(func=cmd_generate)
    sub.add_parser("split", parents=[common, spl], help="split grids into tiles").set_defaults(func=cmd_split)
    sub.add_parser("run", parents=[common, gen, spl], help="generate then split").set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)

"""File naming rules shared by the generate and split steps."""

from __future__ import annotations

import re
from pathlib import Path

_UNSAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_SPACES = re.compile(r"[\s,]+")
_GRID_RE = re.compile(r"^(?P<slug>.+)_grid_(?P<num>\d{3,})$")


def slugify(subject: str, max_len: int = 60) -> str:
    """Turn a free-form subject description into a filesystem-safe name.

    Unicode letters (e.g. Korean) are kept; characters Windows forbids are removed.
    """
    slug = _UNSAFE.sub("", subject)
    slug = _SPACES.sub("_", slug).strip("._ ")
    slug = slug[:max_len].rstrip("._ ")
    return slug or "subject"


def grid_stem(slug: str, batch_no: int) -> str:
    return f"{slug}_grid_{batch_no:03d}"


def tile_name(grid_stem_name: str, row: int, col: int) -> str:
    return f"{grid_stem_name}_r{row:02d}_c{col:02d}.png"


def next_batch_numbers(slug: str, count: int, grid_dir: Path) -> list[int]:
    """Batch numbers that continue after the existing grids, so nothing is overwritten."""
    existing = [
        int(m.group("num"))
        for p in grid_dir.glob(f"{slug}_grid_*.png")
        if (m := _GRID_RE.match(p.stem)) and m.group("slug") == slug
    ]
    start = max(existing, default=0) + 1
    return list(range(start, start + count))

"""Step 2: cut grid images into individual training tiles."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from gridgen.naming import tile_name

Box = tuple[int, int, int, int]  # (left, upper, right, lower)


def tile_boxes(width: int, height: int, rows: int, cols: int, inner_crop: float = 0.0) -> list[tuple[int, int, Box]]:
    """Compute crop boxes for every cell as (row, col, box), 1-indexed.

    Cell edges are distributed with integer division so the whole image is covered even
    when width/height are not divisible by cols/rows. `inner_crop` trims that fraction
    from each side of a cell to drop separator lines and bleed from neighbouring cells.
    """
    inner_crop = max(0.0, min(0.4, inner_crop))
    xs = [c * width // cols for c in range(cols + 1)]
    ys = [r * height // rows for r in range(rows + 1)]

    boxes = []
    for r in range(rows):
        for c in range(cols):
            left, right, upper, lower = xs[c], xs[c + 1], ys[r], ys[r + 1]
            pad_x = int((right - left) * inner_crop)
            pad_y = int((lower - upper) * inner_crop)
            boxes.append((r + 1, c + 1, (left + pad_x, upper + pad_y, right - pad_x, lower - pad_y)))
    return boxes


def split_grid(
    grid_path: Path,
    out_dir: Path,
    rows: int,
    cols: int,
    tile_size: int,
    inner_crop: float = 0.0,
    overwrite: bool = False,
) -> int:
    """Split one grid image. Returns the number of tiles written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = grid_path.stem

    written = 0
    with Image.open(grid_path) as img:
        targets = [
            (box, out_dir / tile_name(stem, r, c))
            for r, c, box in tile_boxes(img.width, img.height, rows, cols, inner_crop)
        ]
        if not overwrite and all(path.exists() for _, path in targets):
            print(f"[SKIP] {grid_path.name} already split")
            return 0

        img = img.convert("RGB")
        for box, path in targets:
            if path.exists() and not overwrite:
                continue
            img.crop(box).resize((tile_size, tile_size), Image.Resampling.LANCZOS).save(path)
            written += 1
    print(f"[OK] {grid_path.name} -> {written} tiles")
    return written


def split_all(grid_dir: Path, out_dir: Path, rows: int, cols: int, tile_size: int,
              inner_crop: float = 0.0, overwrite: bool = False, pattern: str = "*.png") -> int:
    grids = sorted(grid_dir.glob(pattern))
    if not grids:
        print(f"[WARN] no grid images matching '{pattern}' in {grid_dir}")
        return 0
    total = sum(split_grid(g, out_dir, rows, cols, tile_size, inner_crop, overwrite) for g in grids)
    print(f"[DONE] {total} tiles written to {out_dir}")
    return total

from PIL import Image

from gridgen.split import split_grid, tile_boxes


def test_boxes_cover_image_without_gaps():
    boxes = tile_boxes(1000, 1000, rows=3, cols=3)
    assert len(boxes) == 9
    # 1000 is not divisible by 3; edges must still meet exactly and reach the border.
    assert boxes[0][2][0] == 0 and boxes[-1][2][2] == 1000
    for (_, _, a), (_, _, b) in zip(boxes[0:2], boxes[1:3]):
        assert a[2] == b[0]


def test_inner_crop_trims_each_side():
    (_, _, box), *_ = tile_boxes(400, 400, rows=2, cols=2, inner_crop=0.1)
    assert box == (20, 20, 180, 180)


def test_inner_crop_is_clamped():
    (_, _, box), *_ = tile_boxes(400, 400, rows=1, cols=1, inner_crop=0.9)
    assert box == (160, 160, 240, 240)  # clamped to 0.4


def test_split_grid_writes_tiles_and_skips_second_time(tmp_path):
    grid = tmp_path / "apple_grid_001.png"
    Image.new("RGB", (200, 200), "red").save(grid)
    out = tmp_path / "tiles"

    assert split_grid(grid, out, rows=2, cols=2, tile_size=64) == 4
    assert (out / "apple_grid_001_r02_c02.png").exists()
    with Image.open(out / "apple_grid_001_r01_c01.png") as tile:
        assert tile.size == (64, 64)
    assert split_grid(grid, out, rows=2, cols=2, tile_size=64) == 0

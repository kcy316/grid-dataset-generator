from gridgen.naming import grid_stem, next_batch_numbers, slugify, tile_name


def test_slugify_removes_windows_forbidden_chars():
    assert slugify('red apple: "sliced" / on plate?') == "red_apple_sliced_on_plate"


def test_slugify_keeps_unicode_and_limits_length():
    assert slugify("사과, 껍질 깐 상태") == "사과_껍질_깐_상태"
    assert len(slugify("a" * 200)) == 60
    assert slugify("???") == "subject"


def test_names():
    stem = grid_stem("apple", 7)
    assert stem == "apple_grid_007"
    assert tile_name(stem, 1, 12) == "apple_grid_007_r01_c12.png"


def test_next_batch_numbers_continues_after_existing(tmp_path):
    for name in ["apple_grid_001.png", "apple_grid_004.png", "apple_pie_grid_009.png"]:
        (tmp_path / name).touch()
    assert next_batch_numbers("apple", 2, tmp_path) == [5, 6]
    assert next_batch_numbers("banana", 2, tmp_path) == [1, 2]

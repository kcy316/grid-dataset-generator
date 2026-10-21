import json

from gridgen.config import load_settings
from gridgen.generate import generate_subject
from gridgen.prompts import build_grid_prompt


def test_prompt_mentions_grid_shape_and_subject():
    prompt = build_grid_prompt("a red apple", rows=5, cols=5, variation="Use kitchen counters.")
    assert "5x5 grid of 25" in prompt
    assert "a red apple" in prompt
    assert "Use kitchen counters." in prompt


def test_dry_run_writes_manifest_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # make sure no real .env is picked up
    settings = load_settings().with_overrides(output_dir=tmp_path / "out", api_key=None)

    manifest_path = generate_subject(settings, "red apple", batches=2, dry_run=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [b["batch"] for b in manifest["batches"]] == [1, 2]
    assert all(b["status"] == "dry_run" for b in manifest["batches"])
    assert not list((tmp_path / "out" / "grids").glob("*.png"))

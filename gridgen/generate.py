"""Step 1: generate grid images with the OpenAI Images API."""

from __future__ import annotations

import base64
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from gridgen.config import Settings
from gridgen.naming import grid_stem, next_batch_numbers, slugify
from gridgen.prompts import (
    DEFAULT_VARIATION,
    VARIATION_SYSTEM_PROMPT,
    build_grid_prompt,
    build_variation_request,
    style_for_batch,
)


def _make_client(settings: Settings):
    from openai import OpenAI  # imported lazily so --dry-run works without network setup

    return OpenAI(api_key=settings.require_api_key())


def make_variation(client, settings: Settings, subject: str, batch_no: int) -> tuple[str, str]:
    """Ask a text model for batch-specific direction. Falls back to a static preset on failure.

    Returns (variation_text, source) where source is "llm", "preset" or "default".
    """
    style = style_for_batch(batch_no)
    if client is None or not settings.use_llm_variation:
        return f"Visual style: {style}. {DEFAULT_VARIATION}", "preset"

    try:
        response = client.responses.create(
            model=settings.text_model,
            input=[
                {"role": "system", "content": VARIATION_SYSTEM_PROMPT},
                {"role": "user", "content": build_variation_request(subject, batch_no, style)},
            ],
        )
        text = response.output_text.strip()
        if text:
            return text, "llm"
    except Exception as e:  # network/model errors should not stop image generation
        print(f"[WARN] variation request failed for batch {batch_no}: {e}")
    return f"Visual style: {style}. {DEFAULT_VARIATION}", "default"


def _save_image(item, path: Path) -> None:
    if getattr(item, "b64_json", None):
        path.write_bytes(base64.b64decode(item.b64_json))
        return
    if getattr(item, "url", None):
        with urllib.request.urlopen(item.url, timeout=120) as resp:
            path.write_bytes(resp.read())
        return
    raise RuntimeError("Image response contained neither b64_json nor url.")


def generate_subject(settings: Settings, subject: str, batches: int, dry_run: bool = False) -> Path:
    """Generate `batches` grid images for one subject. Returns the manifest path."""
    for d in (settings.grid_dir, settings.manifest_dir):
        d.mkdir(parents=True, exist_ok=True)

    client = None if dry_run else _make_client(settings)
    slug = slugify(subject)
    batch_numbers = (
        list(range(1, batches + 1))
        if settings.overwrite
        else next_batch_numbers(slug, batches, settings.grid_dir)
    )

    started = datetime.now()
    records = []
    print(f"[START] '{subject}' -> batches {batch_numbers}{' (dry run)' if dry_run else ''}")

    for batch_no in batch_numbers:
        variation, source = make_variation(client, settings, subject, batch_no)
        prompt = build_grid_prompt(subject, settings.rows, settings.cols, variation)
        path = settings.grid_dir / f"{grid_stem(slug, batch_no)}.png"
        record = {"batch": batch_no, "file": path.name, "variation_source": source, "prompt": prompt}

        if dry_run:
            record["status"] = "dry_run"
            print(f"[DRY RUN] batch {batch_no}\n{prompt}")
        else:
            record["status"] = _generate_with_retry(client, settings, prompt, path)
            time.sleep(settings.sleep_seconds)
        records.append(record)

    finished = datetime.now()
    ok = sum(r["status"] == "ok" for r in records)
    manifest = {
        "subject": subject,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "image_model": settings.image_model,
        "image_size": settings.image_size,
        "image_quality": settings.image_quality,
        "text_model": settings.text_model if settings.use_llm_variation else None,
        "grid": f"{settings.rows}x{settings.cols}",
        "succeeded": ok,
        "images_expected": ok * settings.cells,
        "batches": records,
    }
    manifest_path = settings.manifest_dir / f"{started:%Y%m%d_%H%M%S}_{slug}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] {ok}/{len(records)} grids for '{subject}'. Manifest: {manifest_path}")
    return manifest_path


def _generate_with_retry(client, settings: Settings, prompt: str, path: Path) -> str:
    if path.exists() and not settings.overwrite:
        print(f"[SKIP] {path.name} already exists")
        return "skipped"

    for attempt in range(1, settings.retries + 1):
        try:
            response = client.images.generate(
                model=settings.image_model,
                prompt=prompt,
                size=settings.image_size,
                quality=settings.image_quality,
            )
            _save_image(response.data[0], path)
            print(f"[OK] {path.name}")
            return "ok"
        except Exception as e:
            print(f"[ERROR] {path.name} attempt {attempt}/{settings.retries}: {e}")
            if attempt < settings.retries:
                time.sleep(5 * attempt)
    return "failed"

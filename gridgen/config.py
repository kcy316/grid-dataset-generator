"""Runtime settings, loaded from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    image_model: str
    text_model: str
    image_size: str
    image_quality: str
    use_llm_variation: bool
    rows: int
    cols: int
    tile_size: int
    inner_crop: float
    retries: int
    sleep_seconds: float
    overwrite: bool
    output_dir: Path

    @property
    def grid_dir(self) -> Path:
        return self.output_dir / "grids"

    @property
    def tile_dir(self) -> Path:
        return self.output_dir / "tiles"

    @property
    def manifest_dir(self) -> Path:
        return self.output_dir / "manifests"

    @property
    def cells(self) -> int:
        return self.rows * self.cols

    def with_overrides(self, **kwargs) -> "Settings":
        """Return a copy with every non-None keyword argument applied."""
        return replace(self, **{k: v for k, v in kwargs.items() if v is not None})

    def require_api_key(self) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key, "
                "or run with --dry-run to preview prompts without calling the API."
            )
        return self.api_key


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or Path.cwd() / ".env")
    return Settings(
        api_key=os.getenv("OPENAI_API_KEY") or None,
        image_model=os.getenv("IMAGE_MODEL", "gpt-image-2"),
        text_model=os.getenv("TEXT_MODEL", "gpt-5.5"),
        image_size=os.getenv("IMAGE_SIZE", "2560x2560"),
        image_quality=os.getenv("IMAGE_QUALITY", "medium"),
        use_llm_variation=os.getenv("USE_LLM_VARIATION", "true").lower() == "true",
        rows=_env_int("GRID_ROWS", 4),
        cols=_env_int("GRID_COLS", 4),
        tile_size=_env_int("TILE_SIZE", 640),
        inner_crop=_env_float("INNER_CROP", 0.06),
        retries=_env_int("RETRIES", 3),
        sleep_seconds=_env_float("SLEEP_SECONDS", 2.0),
        overwrite=os.getenv("OVERWRITE", "false").lower() == "true",
        output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
    )

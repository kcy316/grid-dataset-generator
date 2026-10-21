"""Prompt templates for grid image generation."""

from __future__ import annotations

# Each batch is pushed toward a different "look" so grids don't resemble each other.
STYLE_PRESETS = [
    "soft overcast daylight, neutral colours, low contrast",
    "warm indoor tungsten light, cosy evening atmosphere",
    "cold bluish LED light, clinical and sterile feel",
    "hard midday sun with crisp, dark shadows",
    "direct on-camera flash, dark background, sharp falloff",
    "dim, underexposed scene with visible sensor noise",
    "strong backlight with bright rim highlights",
    "mixed coloured lighting, slightly unbalanced white balance",
    "flat fluorescent office or store lighting",
    "faded, slightly warm vintage film look with grain",
]

DEFAULT_VARIATION = (
    "Use a wide mix of everyday environments, surfaces and lighting conditions, "
    "as if each photo was taken by a different person with a different phone."
)


def style_for_batch(batch_no: int) -> str:
    return STYLE_PRESETS[(batch_no - 1) % len(STYLE_PRESETS)]


def build_grid_prompt(subject: str, rows: int, cols: int, variation: str) -> str:
    n = rows * cols
    return f"""\
Generate a single square image arranged as a {rows}x{cols} grid of {n} separate photographs.
Every photograph shows: {subject}.

Purpose: training data for an object detection model. Prefer realistic, everyday,
imperfect photos over polished advertising shots.

Layout rules:
- Exactly {rows} rows and {cols} columns of equal-sized cells.
- Separate cells with thin, straight, dark lines so the grid can be cut programmatically.
- Nothing may cross from one cell into another.
- No text, numbers, labels, logos or watermarks anywhere.

Variety rules (every cell must differ from all others):
- Camera angle: mix top-down, steep overhead, 45-degree handheld, low-angle and near eye-level views.
- Distance: mix close-ups, medium shots and wider shots where the subject is small in the frame.
- Quantity and arrangement: single items, a few items, piles or groups; some cut off by the frame edge.
- Background and surface: vary materials, colours and amount of clutter.
- Lighting: vary direction, colour temperature and intensity, including imperfect lighting.
- Realistic difficulty: partial occlusion, slight motion blur, reflections, cast shadows.

Batch-specific direction:
{variation}
"""


VARIATION_SYSTEM_PROMPT = """\
You help design diverse synthetic datasets for object detection.
Given a subject and a visual style, write one short English paragraph of photo direction
that is specific to that subject's real-world appearance and where it is typically found.
Avoid advertising or glamour photography. Return only the paragraph."""


def build_variation_request(subject: str, batch_no: int, style: str) -> str:
    return f"""\
Subject: {subject}
Batch: {batch_no}
Visual style: {style}

Describe, in one paragraph:
1. How the visual style should look (light quality, colour temperature, contrast).
2. Three to five realistic places or surfaces where this subject actually appears.
3. Two or three camera angle and distance combinations that suit the subject.
4. Two or three look-alike or commonly nearby objects to place at the edges or background,
   so a detector learns to tell the subject apart from them."""

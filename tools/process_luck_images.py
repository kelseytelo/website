#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS_DIR = ROOT / "images" / "what-is-luck" / "originals"
PROCESSED_DIR = ROOT / "images" / "what-is-luck" / "processed"
IMAGE_LIST = ROOT / "luck.js"

CANVAS_SIZE = (1200, 900)
PADDING = 64
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "luck-image"


def supported_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def fit_on_canvas(image: Image.Image) -> Image.Image:
    canvas_width, canvas_height = CANVAS_SIZE
    max_size = (canvas_width - PADDING * 2, canvas_height - PADDING * 2)
    source = ImageOps.exif_transpose(image).convert("RGBA")
    fitted = ImageOps.contain(source, max_size, method=Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    offset = (
        (canvas_width - fitted.width) // 2,
        (canvas_height - fitted.height) // 2,
    )
    canvas.alpha_composite(fitted, offset)
    return canvas


def process_image(path: Path, index: int) -> dict[str, str]:
    image = Image.open(path)
    filename = f"{index:02d}-{slugify(path.stem)}.png"
    output_path = PROCESSED_DIR / filename
    fit_on_canvas(image).save(output_path, optimize=True)
    return {"src": f"images/what-is-luck/processed/{filename}"}


def write_image_list(entries: list[dict[str, str]]) -> None:
    lines = ["window.luckImages = ["]
    for entry in entries:
        lines.append(f"  {json.dumps(entry, ensure_ascii=False)},")
    lines.append("];")
    lines.append("")
    IMAGE_LIST.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in PROCESSED_DIR.rglob("*.png"):
        old_file.unlink()

    entries = [
        process_image(path, index)
        for index, path in enumerate(supported_images(ORIGINALS_DIR), 1)
    ]
    write_image_list(entries)
    print(f"Processed {len(entries)} What is luck? image(s).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS_DIR = ROOT / "images" / "library" / "originals"
FRONT_DIR = ORIGINALS_DIR / "front"
BACK_DIR = ORIGINALS_DIR / "back"
PROCESSED_DIR = ROOT / "images" / "library" / "processed"
PROCESSED_FRONT_DIR = PROCESSED_DIR / "front"
PROCESSED_BACK_DIR = PROCESSED_DIR / "back"
PHOTO_LIST = ROOT / "photos.js"

CANVAS_SIZE = (1200, 900)
PADDING = 84
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "library-photo"


def caption_from_name(path: Path) -> str:
    words = re.sub(r"[-_]+", " ", path.stem)
    words = re.sub(r"^\s*\d+\s+", "", words).strip()
    return words.title() if words else "Caption"


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


def supported_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def matching_back_cover(front_path: Path) -> Path | None:
    slug = slugify(front_path.stem)
    for path in supported_images(BACK_DIR):
        if slugify(path.stem) == slug:
            return path

    return None


def process_image(path: Path, output_dir: Path, index: int, side: str) -> str:
    image = Image.open(path)
    processed = fit_on_canvas(image)

    filename = f"{index:02d}-{slugify(path.stem)}-{side}.png"
    output_path = output_dir / filename
    processed.save(output_path, optimize=True)
    return f"images/library/processed/{side}/{filename}"


def process_book(front_path: Path, index: int) -> dict[str, str]:
    entry = {
        "src": process_image(front_path, PROCESSED_FRONT_DIR, index, "front"),
        "caption": caption_from_name(front_path),
    }
    back_path = matching_back_cover(front_path)
    if back_path:
        entry["backSrc"] = process_image(back_path, PROCESSED_BACK_DIR, index, "back")
    return {
        key: value
        for key, value in entry.items()
        if value
    }


def write_photo_list(entries: list[dict[str, str]]) -> None:
    lines = ["window.archivePhotos = ["]
    for entry in entries:
        lines.append(f"  {json.dumps(entry, ensure_ascii=False)},")
    lines.append("];")
    lines.append("")
    PHOTO_LIST.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    FRONT_DIR.mkdir(parents=True, exist_ok=True)
    BACK_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_FRONT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_BACK_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in PROCESSED_DIR.rglob("*.png"):
        old_file.unlink()

    originals = supported_images(FRONT_DIR)
    if not originals:
        originals = supported_images(ORIGINALS_DIR)

    entries = [process_book(path, index) for index, path in enumerate(originals, 1)]
    write_photo_list(entries)
    print(f"Processed {len(entries)} Library photo(s).")


if __name__ == "__main__":
    main()

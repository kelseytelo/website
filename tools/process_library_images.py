#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

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


def estimate_background(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    patch_size = max(16, min(width, height) // 18)
    patches = [
        rgb.crop((0, 0, patch_size, patch_size)),
        rgb.crop((width - patch_size, 0, width, patch_size)),
        rgb.crop((0, height - patch_size, patch_size, height)),
        rgb.crop((width - patch_size, height - patch_size, width, height)),
    ]

    samples = []
    for patch in patches:
        sample = patch.resize((2, 2), Image.Resampling.BOX)
        pixels = sample.load()
        samples.extend(pixels[x, y] for y in range(2) for x in range(2))

    channels = list(zip(*samples))
    return tuple(int(sorted(channel)[len(channel) // 2]) for channel in channels)


def inner_union_bbox(mask: Image.Image) -> tuple[int, int, int, int] | None:
    width, height = mask.size
    pixels = mask.load()
    seen = bytearray(width * height)
    min_area = max(80, round(width * height * 0.001))
    union: tuple[int, int, int, int] | None = None

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if seen[index] or pixels[x, y] == 0:
                continue

            stack = [(x, y)]
            seen[index] = 1
            area = 0
            left = right = x
            top = bottom = y
            touches_edge = False

            while stack:
                current_x, current_y = stack.pop()
                area += 1
                left = min(left, current_x)
                right = max(right, current_x)
                top = min(top, current_y)
                bottom = max(bottom, current_y)

                if (
                    current_x == 0
                    or current_y == 0
                    or current_x == width - 1
                    or current_y == height - 1
                ):
                    touches_edge = True

                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue

                    next_index = next_y * width + next_x
                    if seen[next_index] or pixels[next_x, next_y] == 0:
                        continue

                    seen[next_index] = 1
                    stack.append((next_x, next_y))

            if touches_edge:
                continue

            if area < min_area:
                continue

            component = (left, top, right + 1, bottom + 1)
            if union is None:
                union = component
            else:
                union = (
                    min(union[0], component[0]),
                    min(union[1], component[1]),
                    max(union[2], component[2]),
                    max(union[3], component[3]),
                )

    return union


def rectangular_crop(image: Image.Image) -> Image.Image:
    source = ImageOps.exif_transpose(image).convert("RGB")
    width, height = source.size
    max_side = max(width, height)
    scale = min(1.0, 760 / max_side)
    work = source

    if scale < 1:
        work = source.resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.BOX,
        )

    background = Image.new("RGB", work.size, estimate_background(work))
    diff = ImageChops.difference(work, background).convert("L")
    stat = ImageStat.Stat(diff)
    threshold = max(24, min(80, int(stat.mean[0] + stat.stddev[0] * 0.45)))
    mask = diff.point(lambda pixel: 255 if pixel > threshold else 0)
    mask = mask.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(9))

    bbox = inner_union_bbox(mask) or mask.getbbox()
    if not bbox:
        return ImageOps.exif_transpose(image).convert("RGBA")

    left, top, right, bottom = bbox
    if scale < 1:
        left = math.floor(left / scale)
        top = math.floor(top / scale)
        right = math.ceil(right / scale)
        bottom = math.ceil(bottom / scale)

    margin = max(8, round(max(width, height) * 0.005))
    crop_box = (
        max(0, left - margin),
        max(0, top - margin),
        min(width, right + margin),
        min(height, bottom + margin),
    )
    return ImageOps.exif_transpose(image).convert("RGBA").crop(crop_box)


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
    processed = fit_on_canvas(rectangular_crop(image))

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

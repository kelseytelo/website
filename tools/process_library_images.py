#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS_DIR = ROOT / "images" / "library" / "originals"
PROCESSED_DIR = ROOT / "images" / "library" / "processed"
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


def largest_inner_component_bbox(mask: Image.Image) -> tuple[int, int, int, int] | None:
    width, height = mask.size
    max_side = max(width, height)
    scale = min(1.0, 900 / max_side)
    work = mask
    if scale < 1:
        work = mask.resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.NEAREST,
        )

    work_width, work_height = work.size
    pixels = work.load()
    seen = bytearray(work_width * work_height)
    best: tuple[int, int, int, int, int] | None = None

    for y in range(work_height):
        for x in range(work_width):
            index = y * work_width + x
            if seen[index] or pixels[x, y] == 0:
                continue

            stack = [(x, y)]
            seen[index] = 1
            area = 0
            left = right = x
            top = bottom = y
            touches_border = False

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
                    or current_x == work_width - 1
                    or current_y == work_height - 1
                ):
                    touches_border = True

                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < work_width and 0 <= next_y < work_height):
                        continue

                    next_index = next_y * work_width + next_x
                    if seen[next_index] or pixels[next_x, next_y] == 0:
                        continue

                    seen[next_index] = 1
                    stack.append((next_x, next_y))

            if touches_border:
                continue

            if best is None or area > best[0]:
                best = (area, left, top, right + 1, bottom + 1)

    if best is None:
        return None

    _, left, top, right, bottom = best
    if scale < 1:
        return (
            max(0, math.floor(left / scale)),
            max(0, math.floor(top / scale)),
            min(width, math.ceil(right / scale)),
            min(height, math.ceil(bottom / scale)),
        )

    return (left, top, right, bottom)


def estimate_background(image: Image.Image) -> tuple[int, int, int]:
    image = image.convert("RGB")
    width, height = image.size
    sample_width = max(1, min(width, max(width // 16, 12)))
    sample_height = max(1, min(height, max(height // 16, 12)))

    strips = [
        image.crop((0, 0, width, sample_height)),
        image.crop((0, height - sample_height, width, height)),
        image.crop((0, 0, sample_width, height)),
        image.crop((width - sample_width, 0, width, height)),
    ]

    samples = []
    for strip in strips:
        samples.extend(strip.resize((1, 1), Image.Resampling.BOX).getdata())

    channels = list(zip(*samples))
    return tuple(int(sorted(channel)[len(channel) // 2]) for channel in channels)


def foreground_mask(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, estimate_background(rgb))
    diff = ImageChops.difference(rgb, background).convert("L")

    stat = ImageStat.Stat(diff)
    threshold = max(18, min(70, int(stat.mean[0] + stat.stddev[0] * 0.65)))
    mask = diff.point(lambda pixel: 255 if pixel > threshold else 0)

    # Smooth small scanner noise and slightly expand the detected book edge.
    mask = mask.filter(ImageFilter.BoxBlur(1))
    bbox = mask.getbbox()
    if not bbox:
        return Image.new("L", rgb.size, 255)

    return mask


def dark_subject_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    threshold = max(48, min(170, int(stat.mean[0] - stat.stddev[0] * 0.35)))
    mask = grayscale.point(lambda pixel: 255 if pixel < threshold else 0)
    mask = mask.filter(ImageFilter.MedianFilter(7))
    return largest_inner_component_bbox(mask) or mask.getbbox()


def trim_to_subject(image: Image.Image) -> Image.Image:
    bbox = dark_subject_bbox(image) or foreground_mask(image).getbbox()
    if not bbox:
        return image.convert("RGBA")

    left, top, right, bottom = bbox
    width, height = image.size
    margin = max(8, round(max(width, height) * 0.006))

    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(width, right + margin)
    bottom = min(height, bottom + margin)

    return image.convert("RGBA").crop((left, top, right, bottom))


def fit_on_canvas(image: Image.Image) -> Image.Image:
    canvas_width, canvas_height = CANVAS_SIZE
    max_width = canvas_width - PADDING * 2
    max_height = canvas_height - PADDING * 2

    scale = min(max_width / image.width, max_height / image.height)
    fitted_size = (
        max(1, math.floor(image.width * scale)),
        max(1, math.floor(image.height * scale)),
    )
    fitted = image.resize(fitted_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    offset = (
        (canvas_width - fitted.width) // 2,
        (canvas_height - fitted.height) // 2,
    )
    canvas.alpha_composite(fitted, offset)
    return canvas


def process_image(path: Path, index: int) -> dict[str, str]:
    image = Image.open(path)
    processed = fit_on_canvas(trim_to_subject(image))

    filename = f"{index:02d}-{slugify(path.stem)}.png"
    output_path = PROCESSED_DIR / filename
    processed.save(output_path, optimize=True)

    return {
        "src": f"images/library/processed/{filename}",
        "caption": caption_from_name(path),
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
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in PROCESSED_DIR.glob("*.png"):
        old_file.unlink()

    originals = sorted(
        path
        for path in ORIGINALS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    entries = [process_image(path, index) for index, path in enumerate(originals, 1)]
    write_photo_list(entries)
    print(f"Processed {len(entries)} Library photo(s).")


if __name__ == "__main__":
    main()

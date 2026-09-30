#!/usr/bin/env python3
"""Inventory an unlabelled local image folder without modifying its source files.

Produces privacy-stripped preview JPEGs, contact sheets, and a local JSON audit.
The output is staging material only; no image becomes morph-training eligible here.
Requires Pillow. On macOS, HEIC decoding uses the system ``sips`` command.
"""

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError


def decode(path):
    try:
        with Image.open(path) as source:
            return ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError):
        if path.suffix.lower() != ".heic":
            raise
    with tempfile.TemporaryDirectory() as temporary:
        converted = Path(temporary) / "converted.jpg"
        result = subprocess.run(
            ["sips", "-s", "format", "jpeg", str(path), "--out", str(converted)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise OSError("HEIC decode failed")
        with Image.open(converted) as source:
            return ImageOps.exif_transpose(source).convert("RGB")


def difference_hash(image):
    small = ImageOps.grayscale(image).resize((9, 8))
    pixels = list(small.tobytes())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return f"{bits:016x}"


def save_sheet(records, output, page):
    columns, rows = 5, 5
    cell_w, cell_h = 210, 184
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "#f6f4ed")
    draw = ImageDraw.Draw(sheet)
    start = page * columns * rows
    for slot, record in enumerate(records[start:start + columns * rows]):
        x, y = (slot % columns) * cell_w, (slot // columns) * cell_h
        with Image.open(output / record["preview"]) as source:
            thumb = ImageOps.contain(source, (cell_w - 12, cell_h - 35))
            sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y + 5))
        draw.text((x + 6, y + cell_h - 26), f"{record['index']:03d}  {record['source_name'][:17]}", fill="#222222")
    destination = output / "sheets" / f"sheet-{page + 1:02d}.jpg"
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=86)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=Path.home() / "Library" / "Application Support" / "HogMorphStudio" / "incoming-review",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    project_root = Path(__file__).resolve().parents[1]
    web_root = project_root.parent
    overlaps = lambda left, right: left == right or left in right.parents or right in left.parents
    if overlaps(output, source):
        parser.error("--output must not be the source folder or overlap its tree")
    if output == project_root or output in project_root.parents or project_root in output.parents:
        parser.error("--output must not overlap the project tree")
    if output == web_root or output in web_root.parents or web_root in output.parents:
        parser.error("--output must not overlap the local web-server root")
    output.mkdir(parents=True, exist_ok=True)
    candidates = sorted(path for path in source.iterdir() if path.is_file())
    records, rejected = [], []
    for index, path in enumerate(candidates, 1):
        try:
            image = decode(path)
        except (OSError, ValueError) as error:
            rejected.append({"source_name": path.name, "reason": type(error).__name__})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        preview = f"previews/{index:03d}-{digest[:12]}.jpg"
        preview_path = output / preview
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        ImageOps.contain(image, (900, 900)).save(preview_path, quality=83)
        records.append({
            "index": index, "source_name": path.name, "source_path": str(path),
            "bytes": path.stat().st_size, "width": image.width, "height": image.height,
            "sha256": digest, "dhash": difference_hash(image), "preview": preview,
            "source_scope": "unknown", "species_review": "pending", "morph_labels": [],
            "individual_id": None, "rights_status": "unknown", "morph_training_eligible": False,
        })
        image.close()
    by_hash = defaultdict(list)
    for record in records:
        by_hash[record["sha256"]].append(record["index"])
    report = {
        "source_folder": str(source), "candidate_files": len(candidates),
        "decoded_images": len(records), "rejected_files": rejected,
        "exact_duplicate_groups": [group for group in by_hash.values() if len(group) > 1],
        "file_extensions": dict(Counter(path.suffix.lower() or "[none]" for path in candidates)),
        "records": records,
        "warning": "Local review staging only. Labels, snake identity and media rights are unknown.",
    }
    (output / "inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for page in range((len(records) + 24) // 25):
        save_sheet(records, output, page)
    print(json.dumps({key: report[key] for key in ("candidate_files", "decoded_images", "rejected_files", "exact_duplicate_groups", "file_extensions")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

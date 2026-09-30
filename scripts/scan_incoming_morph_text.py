#!/usr/bin/env python3
"""Find possible morph-name text in private incoming-photo previews.

OCR is a review-navigation aid only. It never creates a label, validates a
specimen, establishes rights, or makes an image eligible for training.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


# Keep aliases discoverable in English and Simplified Chinese. White Wall is
# intentionally included as a phenotype descriptor, never as a gene.
TERMS: dict[str, tuple[str, ...]] = {
    "Anaconda": ("anaconda", "conda", "康达", "康達"),
    "Superconda": ("superconda", "super conda", "超级康达", "超級康達"),
    "Arctic": ("arctic", "北极", "北極"),
    "Super Arctic": ("super arctic", "superarctic", "超级北极", "超級北極"),
    "Albino": ("albino", "白化"),
    "Axanthic": ("axanthic", "缺黄", "缺黃"),
    "Sable": ("sable", "紫貂", "紫貂"),
    "Toffee Belly": ("toffee belly", "toffeebelly", "太妃糖腹", "太妃糖肚"),
    "Lavender": ("lavender", "薰衣草"),
    "Extreme Red": ("extreme red", "extremered", "极端红", "極端紅"),
    "Lemon Ghost": ("lemon ghost", "lemonghost", "柠檬鬼", "檸檬鬼"),
    "Pink Pastel Albino": ("pink pastel albino", "pink pastel", "粉蜡笔", "粉蠟筆"),
    "Lucy / Leucistic": ("lucy", "leucistic", "露西", "白色型"),
    "Chocolate": ("chocolate", "巧克力"),
    "Skull Face": ("skull face", "skullface", "骷髅脸", "骷髏臉"),
    "Diablo Eyes": ("diablo eyes", "diablo", "魔眼"),
    "White Wall (descriptor)": ("white wall", "whitewall", "白墙", "白牆"),
    "Sunburst": ("sunburst", "日耀", "日耀"),
    "Snow": ("snow",),
    "Yeti": ("yeti", "雪人"),
    "Snowburst": ("snowburst", "雪耀"),
    "Toxic": ("toxic", "毒液"),
    "Mai Tai": ("mai tai", "maitai", "迈泰", "邁泰"),
    "Stormcloud": ("stormcloud", "storm cloud", "风暴云", "風暴雲"),
    "Moonstone": ("moonstone", "月光石"),
    "Coral": ("coral", "珊瑚"),
}


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[^\w\u3400-\u9fff]+", " ", text, flags=re.UNICODE).strip()


def term_matches(line: str) -> list[tuple[str, str]]:
    normalized_line = normalized(line)
    compact_line = normalized_line.replace(" ", "")
    matches: list[tuple[str, str]] = []
    for canonical, aliases in TERMS.items():
        for alias in aliases:
            normalized_alias = normalized(alias)
            if not normalized_alias:
                continue
            if re.fullmatch(r"[a-z0-9 ]+", normalized_alias):
                hit = f" {normalized_line} "
                if f" {normalized_alias} " not in hit:
                    continue
            elif normalized_alias.replace(" ", "") not in compact_line:
                continue
            matches.append((canonical, alias))
            break
    return matches


def line_groups(tsv: str, confidence_floor: float) -> list[tuple[str, float]]:
    grouped: dict[tuple[str, ...], list[tuple[int, str, float]]] = defaultdict(list)
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t")
    for row in reader:
        if row.get("level") != "5" or not row.get("text", "").strip():
            continue
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            continue
        if confidence < confidence_floor:
            continue
        key = tuple(row.get(k, "") for k in ("page_num", "block_num", "par_num", "line_num"))
        grouped[key].append((int(row.get("word_num", "0")), row["text"].strip(), confidence))
    output: list[tuple[str, float]] = []
    for words in grouped.values():
        ordered_rows = sorted(words)
        ordered = [word for _, word, _ in ordered_rows]
        if not ordered:
            continue
        mean_confidence = sum(conf for _, _, conf in ordered_rows) / len(ordered_rows)
        output.append((" ".join(ordered), mean_confidence))
    return output


def ocr_preview(tesseract: str, image: Path, tessdata: Path, language: str, psm: int) -> tuple[list[tuple[str, str, float]], str | None]:
    command = [
        tesseract, str(image), "stdout", "-l", language,
        "--tessdata-dir", str(tessdata), "--oem", "1", "--psm", str(psm), "tsv",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        return [], f"tesseract_exit_{result.returncode}"
    matches: dict[str, tuple[str, float]] = {}
    for text, confidence in line_groups(result.stdout, 20):
        for canonical, alias in term_matches(text):
            current = matches.get(canonical)
            if current is None or confidence > current[1]:
                matches[canonical] = (alias, confidence)
    return [(canonical, alias, confidence) for canonical, (alias, confidence) in sorted(matches.items())], None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True, help="Private active_inventory.json")
    parser.add_argument("--output", type=Path, required=True, help="Private JSON output path")
    parser.add_argument("--tessdata-dir", type=Path, required=True, help="Local tessdata folder containing chi_sim and eng")
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--language", default="chi_sim+eng")
    parser.add_argument("--psm", type=int, default=11)
    parser.add_argument("--include-uncertain", action="store_true", help="Also scan quarantined uncertain-species rows")
    args = parser.parse_args()

    executable = shutil.which(args.tesseract)
    if not executable:
        parser.error(f"Tesseract executable not found: {args.tesseract}")
    inventory_path = args.inventory.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    tessdata = args.tessdata_dir.expanduser().resolve()
    for lang in args.language.split("+"):
        if not (tessdata / f"{lang}.traineddata").is_file():
            parser.error(f"Missing {lang}.traineddata under {tessdata}")
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    allowed_triage = {"candidate_western_hognose"}
    if args.include_uncertain:
        allowed_triage.add("uncertain")

    records = [r for r in data.get("records", []) if r.get("visual_triage") in allowed_triage]
    output_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    scanned = 0
    for record in records:
        rel_preview = Path(record.get("preview", ""))
        image = (inventory_path.parent / rel_preview).resolve()
        if inventory_path.parent.resolve() not in image.parents:
            failures.append({"index": record.get("index"), "reason": "preview_outside_inventory_root"})
            continue
        if not image.is_file():
            failures.append({"index": record.get("index"), "reason": "preview_missing"})
            continue
        scanned += 1
        found, error = ocr_preview(executable, image, tessdata, args.language, args.psm)
        if error:
            failures.append({"index": record.get("index"), "reason": error})
            continue
        if not found:
            continue
        output_records.append({
            "index": record.get("index"),
            "source_sha256": record.get("sha256"),
            "visual_triage": record.get("visual_triage"),
            "possible_morph_terms": [
                {"term": canonical, "recognized_alias": alias,
                 "ocr_line_confidence": round(confidence, 1),
                 "status": "ocr_hint_requires_human_source_review",
                 "training_eligible": False}
                for canonical, alias, confidence in found
            ],
        })
    report = {
        "schema_version": "1.0.0",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "private local OCR hints for manual provenance review only",
        "engine": "Tesseract OCR",
        "language": args.language,
        "records_considered": len(records),
        "images_scanned": scanned,
        "images_with_possible_morph_text": len(output_records),
        "failures": failures,
        "all_hits_require_human_review": True,
        "images_and_recognized_free_text_included": False,
        "training_eligible_records_added": 0,
        "records": output_records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "records_considered", "images_scanned", "images_with_possible_morph_text",
        "failures", "training_eligible_records_added", "output"
    ) if k != "output"}, ensure_ascii=False))
    print(f"Private report: {output_path}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Convert a private photo-review JSON export into gated manifest candidates.

This does not label images, infer rights, or train a model. Every candidate is
matched against the private staged inventory, its original SHA-256 is checked,
and the existing training-manifest validator is applied before it is emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from prepare_training_manifest import ONTOLOGY, TRAITS, validate


DEFAULT_INVENTORY = (
    Path.home() / "Library" / "Application Support" / "HogMorphStudio"
    / "incoming-review" / "reviewed_inventory.json"
)
DEFAULT_OUTPUT = (
    Path.home() / "Library" / "Application Support" / "HogMorphStudio"
    / "training-review" / "eligible-candidates.jsonl"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def contained_preview(inventory_root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.startswith("previews/"):
        raise ValueError("inventory preview path must be under previews/")
    preview_root = inventory_root / "previews"
    if preview_root.is_symlink():
        raise ValueError("preview directory cannot be a symlink")
    unresolved = inventory_root / relative
    if unresolved.is_symlink():
        raise ValueError("preview file cannot be a symlink")
    path = unresolved.resolve(strict=True)
    if preview_root.resolve(strict=True) not in path.parents or not path.is_file():
        raise ValueError("preview path escapes the private preview directory")
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("preview image format is not supported by the training gate")
    return path


def convert_record(review: dict, indexed: dict, inventory_root: Path) -> tuple[dict | None, list[str]]:
    """Translate one exported UI review; keep all missing evidence as rejection."""
    reasons = []
    index = review.get("source_index")
    digest = review.get("source_sha256")
    if type(index) is not int or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        return None, ["review export is missing a valid source_index/source_sha256 pair"]
    source = indexed.get((index, digest))
    if source is None:
        return None, ["source index and SHA-256 do not match the private inventory"]

    if source.get("visual_triage") != "candidate_western_hognose":
        reasons.append("source was not in the Western Hognose candidate queue")
    if review.get("species_review") != "western_hognose":
        reasons.append("manual species review must confirm Western Hognose")
    if review.get("source_scope") != "captive_morph":
        reasons.append("source_scope must be captive_morph")

    original = Path(str(source.get("source_path", "")))
    if not original.is_file():
        reasons.append("original source image is missing")
    elif sha256_file(original) != digest:
        reasons.append("original source image SHA-256 no longer matches inventory")

    try:
        image_path = contained_preview(inventory_root, source.get("preview"))
    except (OSError, RuntimeError, ValueError) as error:
        image_path = None
        reasons.append(f"private preview cannot be used: {error}")

    raw_labels = review.get("morph_labels")
    labels = {}
    if not isinstance(raw_labels, list):
        reasons.append("morph_labels must be a list of reviewed trait/state entries")
    else:
        for entry in raw_labels:
            if not isinstance(entry, dict):
                reasons.append("each morph label must contain trait_id and state")
                continue
            trait, state = entry.get("trait_id"), entry.get("state")
            key = f"{trait}:{state}"
            if not isinstance(trait, str) or not isinstance(state, str) or not state:
                reasons.append("each morph label must contain trait_id and state")
            elif state == "not_recorded":
                # The review UI exposes this ontology state as an explicit way
                # to say "unknown". Unknown is not a trainable class or label.
                inheritance = TRAITS.get(trait, {}).get("inheritance")
                allowed_states = ONTOLOGY["states"].get(inheritance, [])
                if trait not in TRAITS or state not in allowed_states:
                    reasons.append(f"unknown trait/state entry: {key}")
                else:
                    continue
            elif key in labels:
                reasons.append(f"duplicate trait/state entry: {key}")
            else:
                labels[key] = 1

    raw_aliases = review.get("aliases", [])
    aliases = []
    if not isinstance(raw_aliases, list) or any(not isinstance(alias, str) or not alias
                                                for alias in raw_aliases):
        reasons.append("aliases must be a list of non-empty alias IDs")
    else:
        aliases = raw_aliases
        if len(aliases) != len(set(aliases)):
            reasons.append("aliases must not contain duplicate IDs")

    rights_scopes = review.get("rights_scopes")
    if not isinstance(rights_scopes, dict):
        rights_scopes = {}

    record = {
        "id": f"incoming-{index:03d}-{digest[:12]}",
        "image": str(image_path) if image_path else "",
        "source_scope": review.get("source_scope"),
        "source_url": review.get("source_url"),
        "individual_id": review.get("individual_id"),
        "labels": labels,
        "aliases": aliases,
        "genotype_evidence": review.get("evidence_type"),
        "evidence_url": review.get("evidence_url"),
        "claim_scope": review.get("claim_scope"),
        "image_rights": review.get("image_rights"),
        "rights_evidence_url": review.get("rights_evidence_url"),
        "rights_reviewed_by": review.get("rights_reviewed_by"),
        "rights_scopes": {
            name: rights_scopes.get(name)
            for name in ("training", "evaluation", "hackathon_demo", "public_web")
        },
        "attribution": review.get("attribution"),
        "review_status": review.get("review_status"),
        "reviewer": review.get("reviewer"),
    }
    if reasons:
        return None, sorted(set(reasons))

    validated, validation_reasons = validate(record, inventory_root)
    if validation_reasons:
        return None, validation_reasons
    return validated, []


def build_manifest(review_export: dict, inventory: dict, inventory_path: Path) -> dict:
    if not isinstance(review_export, dict) or review_export.get("schema_version") != "incoming-review-v1":
        raise ValueError("review export schema_version must be incoming-review-v1")
    reviews = review_export.get("records")
    if not isinstance(reviews, list) or any(not isinstance(row, dict) for row in reviews):
        raise ValueError("review export records must be a list of objects")
    inventory_records = inventory.get("records") if isinstance(inventory, dict) else None
    if not isinstance(inventory_records, list):
        raise ValueError("private inventory must contain a records list")
    indexed = {}
    for row in inventory_records:
        if not isinstance(row, dict):
            continue
        key = (row.get("index"), row.get("sha256"))
        if key in indexed:
            raise ValueError(f"inventory has duplicate index/SHA identity: {key[0]}")
        indexed[key] = row

    accepted, rejected, seen_source_ids, seen_images = [], [], set(), set()
    for position, review in enumerate(reviews, 1):
        key = (review.get("source_index"), review.get("source_sha256"))
        if key in seen_source_ids:
            rejected.append({"row": position, "source_index": key[0],
                             "reasons": ["duplicate review export entry"]})
            continue
        seen_source_ids.add(key)
        row, reasons = convert_record(review, indexed, inventory_path.parent)
        if row:
            image_digest = sha256_file(Path(row["image"]))
            if image_digest in seen_images:
                reasons = ["duplicate preview image bytes"]
            else:
                seen_images.add(image_digest)
        if reasons:
            rejected.append({"row": position, "source_index": key[0],
                             "reasons": reasons})
        else:
            accepted.append(row)

    reason_counts = Counter(reason for row in rejected for reason in row["reasons"])
    return {
        "schema_version": "reviewed-training-candidates-v1",
        "input_review_records": len(reviews),
        "eligible_candidates": len(accepted),
        "eligible_individuals": len({row["individual_id"] for row in accepted}),
        "rejected_records": len(rejected),
        "rejection_reasons": dict(sorted(reason_counts.items())),
        "records": accepted,
        "rejected": rejected,
        "boundary": "Candidates passed per-record training-manifest validation only. The training script still enforces corpus and class-support gates; no model was trained.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_export", type=Path,
                        help="JSON downloaded from the local incoming-photo review UI")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY,
                        help="private staged inventory; defaults to Application Support")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="private JSONL output; defaults to Application Support")
    parser.add_argument("--report", type=Path,
                        help="JSON audit report; defaults beside --output")
    args = parser.parse_args()
    review_path = args.review_export.expanduser().resolve(strict=True)
    inventory_path = args.inventory.expanduser().resolve(strict=True)
    output_path = args.output.expanduser().resolve()
    report_path = args.report.expanduser().resolve() if args.report else output_path.with_suffix(".report.json")
    protected_paths = {review_path, inventory_path}
    if output_path in protected_paths or report_path in protected_paths or output_path == report_path:
        parser.error("output/report paths must not overwrite an input or each other")
    try:
        result = build_manifest(load_json(review_path), load_json(inventory_path), inventory_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n"
                                    for row in result.pop("records")), encoding="utf-8")
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rejected"},
                     ensure_ascii=False, indent=2))
    if not result["eligible_candidates"]:
        raise SystemExit("No review records passed the existing training-manifest gate")


if __name__ == "__main__":
    main()

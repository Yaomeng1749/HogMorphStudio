#!/usr/bin/env python3
"""Validate reviewed Western hognose image records before model training.

Input: JSON array or JSONL. Output: accepted JSONL and a rejection report.
This never treats blank/omitted labels as negative or a seller name as a genotype.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = json.loads((ROOT / "data" / "ontology.json").read_text())
TRAITS = {t["id"]: t for t in ONTOLOGY["traits"]}
ALIASES = {a["id"]: a for a in ONTOLOGY["aliases"]}
VALID_CLASSES = {
    f"{trait['id']}:{state}"
    for trait in ONTOLOGY["traits"]
    if trait["kind"] != "historical_label"
    for state in trait["states"]
    if state not in {"carrier", "not_recorded"}
}
ALLOWED_RIGHTS = {"owner_permission", "cc0", "cc_by_4_0", "public_domain"}
ALLOWED_EVIDENCE = {"breeder_record", "genetic_test", "expert_phenotype_review"}
RIGHTS_SCOPES = {"training", "evaluation", "hackathon_demo", "public_web"}
SPECIES_MANIFEST = json.loads((ROOT / "data" / "species_manifest.json").read_text())
SPECIES_ONLY_HASHES = {photo["sha256"] for photo in SPECIES_MANIFEST["photos"]}


def load_records(path):
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith("["):
        records = json.loads(raw)
    else:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise ValueError("Input must be an array or JSONL of objects")
    return records


def labels_for(record, reasons):
    labels = record.get("labels")
    if not isinstance(labels, dict):
        reasons.append("labels must be an object with explicit 0/1 values")
        return {}
    selected = {}
    for key, value in labels.items():
        if key not in VALID_CLASSES:
            reasons.append(f"unknown or non-trainable class: {key}")
        elif value is None:
            continue  # unknown is masked, never a negative
        elif type(value) is not int or value not in (0, 1):
            reasons.append(f"label must be 0, 1, or null: {key}")
        else:
            selected[key] = value
    aliases = record.get("aliases", [])
    if not isinstance(aliases, list):
        reasons.append("aliases must be a list")
        aliases = []
    for alias_id in aliases:
        alias = ALIASES.get(alias_id)
        if not alias:
            reasons.append(f"unknown alias: {alias_id}")
            continue
        for part in alias["components"]:
            class_id = f"{part['trait_id']}:{part['state']}"
            if class_id not in VALID_CLASSES or selected.get(class_id) == 0:
                reasons.append(f"alias conflicts with explicit label: {alias_id}")
            else:
                selected[class_id] = 1
    if not any(v == 1 for v in selected.values()):
        reasons.append("at least one reviewed positive morph label is required")
    for locus in ("anaconda", "arctic"):
        one = selected.get(f"{locus}:heterozygous") == 1
        two = selected.get(f"{locus}:homozygous") == 1
        if one and two:
            reasons.append(f"conflicting same-locus states: {locus}")
    return selected


def validate(record, base):
    reasons = []
    image = record.get("image")
    image_path = (base / image).resolve() if isinstance(image, str) and image else None
    if not image_path or not image_path.is_file():
        reasons.append("local image file missing")
    elif image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        reasons.append("unsupported image format")
    elif hashlib.sha256(image_path.read_bytes()).hexdigest() in SPECIES_ONLY_HASHES:
        reasons.append("known species-only reference image is excluded from morph training")
    if record.get("source_scope") != "captive_morph":
        reasons.append("source_scope must be captive_morph")
    for key in ("id", "individual_id", "source_url", "reviewer", "attribution"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            reasons.append(f"missing {key}")
    if record.get("review_status") != "reviewed":
        reasons.append("not reviewed")
    rights = record.get("image_rights")
    if rights not in ALLOWED_RIGHTS:
        reasons.append("image rights do not explicitly permit reuse for this project")
    if rights in ALLOWED_RIGHTS and not record.get("rights_evidence_url"):
        reasons.append("missing rights_evidence_url")
    if not isinstance(record.get("rights_reviewed_by"), str) or not record["rights_reviewed_by"].strip():
        reasons.append("missing rights_reviewed_by")
    rights_scopes = record.get("rights_scopes")
    if not isinstance(rights_scopes, dict) or set(rights_scopes) != RIGHTS_SCOPES or any(type(value) is not bool for value in rights_scopes.values()):
        reasons.append("rights_scopes must explicitly record training, evaluation, hackathon_demo, and public_web as booleans")
        rights_scopes = None
    elif not (rights_scopes["training"] and rights_scopes["evaluation"]):
        reasons.append("image rights do not permit both model training and evaluation")
    evidence = record.get("genotype_evidence")
    if evidence not in ALLOWED_EVIDENCE or not record.get("evidence_url"):
        reasons.append("missing morph evidence type or evidence_url")
    selected = labels_for(record, reasons)
    if evidence == "expert_phenotype_review" and record.get("claim_scope") != "phenotype":
        reasons.append("expert photo review can support phenotype only")
    if any(key.endswith(":carrier") for key in selected):
        reasons.append("carrier state is invisible in photos")
    if reasons:
        return None, sorted(set(reasons))
    return {
        "id": record["id"], "image": str(image_path),
        "individual_id": record["individual_id"], "labels": selected,
        "source_scope": "captive_morph",
        "source_url": record["source_url"], "image_rights": rights,
        "rights_evidence_url": record.get("rights_evidence_url"),
        "rights_reviewed_by": record["rights_reviewed_by"],
        "rights_scopes": rights_scopes,
        "attribution": record["attribution"],
        "genotype_evidence": evidence, "evidence_url": record["evidence_url"],
        "claim_scope": record.get("claim_scope", "phenotype"),
        "review_status": "reviewed",
        "reviewer": record["reviewer"],
    }, []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    records = load_records(args.input)
    accepted, rejected = [], []
    seen_ids, seen_hashes = set(), set()
    for index, record in enumerate(records):
        item, reasons = validate(record, args.input.resolve().parent)
        record_id = str(record.get("id", f"row-{index + 1}"))
        if record_id in seen_ids:
            reasons.append("duplicate record id")
        seen_ids.add(record_id)
        if item:
            digest = hashlib.sha256(Path(item["image"]).read_bytes()).hexdigest()
            if digest in seen_hashes:
                reasons.append("duplicate image bytes")
            seen_hashes.add(digest)
        if reasons:
            rejected.append({"id": record_id, "reasons": sorted(set(reasons))})
        else:
            accepted.append(item)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in accepted))
    reasons = Counter(reason for r in rejected for reason in r["reasons"])
    report = {"input_records": len(records), "accepted_images": len(accepted),
              "accepted_individuals": len({r["individual_id"] for r in accepted}),
              "rejected_images": len(rejected), "rejection_reasons": dict(reasons),
              "rejected": rejected}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rejected"}, indent=2))
    if not accepted:
        raise SystemExit("No eligible morph training images; see rejection report")


if __name__ == "__main__":
    main()

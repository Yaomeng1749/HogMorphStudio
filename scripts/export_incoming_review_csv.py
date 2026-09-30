#!/usr/bin/env python3
"""Export a private, fillable per-photo review CSV from local intake inventory."""

import argparse
import csv
import itertools
import json
from pathlib import Path


FIELDS = [
    "source_index", "source_name", "source_sha256", "visual_triage",
    "potential_duplicate_group", "similarity_review",
    "species_review", "source_scope", "individual_id", "morph_labels",
    "evidence_type", "evidence_url", "claim_scope", "image_rights",
    "rights_evidence_url", "rights_reviewed_by", "rights_training",
    "rights_evaluation", "rights_hackathon_demo", "rights_public_web",
    "attribution", "review_status", "reviewer", "notes",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    candidates = [r for r in inventory["records"] if r.get("visual_triage") == "candidate_western_hognose"]
    active_records = [r for r in inventory["records"] if r.get("visual_triage") in {"candidate_western_hognose", "uncertain"}]
    related = {}
    for first, second in itertools.combinations(active_records, 2):
        distance = (int(first["dhash"], 16) ^ int(second["dhash"], 16)).bit_count()
        if distance <= 10:
            group = f"visual-pair-{min(first['index'], second['index']):03d}-{max(first['index'], second['index']):03d}"
            note = "exact duplicate bytes" if distance == 0 else f"dHash distance {distance}; verify individual identity"
            related[first["index"]] = (group, note)
            related[second["index"]] = (group, note)
    candidate_ids = {record["index"] for record in candidates}
    for pair in inventory.get("manual_similarity_pairs", []):
        first_id, second_id = pair["indices"]
        if first_id not in candidate_ids or second_id not in candidate_ids:
            continue
        group = f"visual-pair-{min(first_id, second_id):03d}-{max(first_id, second_id):03d}"
        note = pair.get("note", "manual visual similarity review; verify individual identity")
        related[first_id] = (group, note)
        related[second_id] = (group, note)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in inventory["records"]:
            writer.writerow({
                "source_index": record["index"],
                "source_name": record["source_name"],
                "source_sha256": record["sha256"],
                "visual_triage": record.get("visual_triage", "pending"),
                "potential_duplicate_group": related.get(record["index"], ("", ""))[0],
                "similarity_review": related.get(record["index"], ("", ""))[1],
                "species_review": "", "source_scope": "", "individual_id": "",
                "morph_labels": "", "evidence_type": "", "evidence_url": "",
                "claim_scope": "", "image_rights": "", "rights_evidence_url": "",
                "rights_reviewed_by": "", "rights_training": "",
                "rights_evaluation": "", "rights_hackathon_demo": "",
                "rights_public_web": "", "attribution": "", "review_status": "",
                "reviewer": "", "notes": "",
            })
    print(f"Wrote {len(inventory['records'])} review rows to {args.output}")


if __name__ == "__main__":
    main()

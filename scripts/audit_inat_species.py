#!/usr/bin/env python3
"""Read-only audit of openly licensed iNaturalist Western Hognose observations.

This script finds candidate records from metadata only. It does not download
photos, assign morph labels, or grant reuse rights beyond each photo's license.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone


API_URL = "https://api.inaturalist.org/v1/observations"
LICENSES = "cc0,cc-by,cc-by-sa"
PAGE_SIZE = 200
MORPH_TERMS = re.compile(
    r"\b(albino|anaconda|conda|sable|arctic|axanthic|lavender|toffee|"
    r"snow|superconda|het|heterozygous)\b",
    re.IGNORECASE,
)


def fetch_page(params: dict[str, object]) -> dict:
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HogMorphStudio metadata-only source audit"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Unexpected iNaturalist API response shape")
    return payload


def audit(max_records: int) -> dict:
    params: dict[str, object] = {
        "taxon_id": 29927,
        "photo_license": LICENSES,
        "per_page": PAGE_SIZE,
        "order": "desc",
        "order_by": "created_at",
        "page": 1,
    }
    first = fetch_page(params)
    total = int(first.get("total_results", 0))
    target = min(total, max_records)
    results = list(first["results"][:target])
    pages = math.ceil(target / PAGE_SIZE)
    for page in range(2, pages + 1):
        time.sleep(1.1)
        params["page"] = page
        results.extend(fetch_page(params).get("results", []))
    results = results[:target]

    license_counts: Counter[str] = Counter()
    captive_ids: list[int] = []
    morph_hits: list[dict[str, object]] = []
    quality_counts: Counter[str] = Counter()
    photo_total = 0
    for observation in results:
        observation_id = observation.get("id")
        quality_counts[str(observation.get("quality_grade") or "unknown")] += 1
        if observation.get("captive"):
            captive_ids.append(observation_id)
        photos = observation.get("photos") or []
        photo_total += len(photos)
        for photo in photos:
            license_counts[str(photo.get("license_code") or "unknown")] += 1
        # Search the observer-authored description only. Place names and taxon
        # guesses are excluded so a location/taxon name cannot look like a morph.
        description = str(observation.get("description") or "")
        matches = sorted({m.group(0).lower() for m in MORPH_TERMS.finditer(description)})
        if matches:
            morph_hits.append({"observation_id": observation_id, "terms": matches})

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "query_url": API_URL,
        "query": {
            "taxon_id": 29927,
            "photo_license": LICENSES,
            "per_page": PAGE_SIZE,
            "order": "desc",
            "order_by": "created_at",
        },
        "total_results_reported": total,
        "records_scanned": len(results),
        "truncated": len(results) < total,
        "observations_with_licensed_photo": len(results),
        "photo_assets_returned": photo_total,
        "photo_license_counts": dict(sorted(license_counts.items())),
        "quality_grade_counts": dict(sorted(quality_counts.items())),
        "captive_marked_observation_ids": sorted(captive_ids),
        "morph_term_observation_hits": morph_hits,
        "interpretation": (
            "Metadata search leads only. Captive flags and morph-name text do not "
            "verify breeder provenance, an individual animal, genotype, or image reuse scope."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-records",
        type=int,
        default=1000,
        help="Maximum observations to scan (default: 1000).",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON output path; without it, print the report to stdout.",
    )
    args = parser.parse_args()
    if args.max_records < 1:
        parser.error("--max-records must be at least 1")
    try:
        report = audit(args.max_records)
    except Exception as exc:  # Surface network/API errors with a concise message.
        print(f"iNaturalist audit failed: {exc}", file=sys.stderr)
        return 1
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(serialized)
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

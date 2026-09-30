#!/usr/bin/env python3
"""Fetch a reviewed, captive, species-only iNaturalist reference subset.

These photographs are not morph labels and must never enter the morph trainer.
The reviewed photo-ID allowlist below is deliberately fixed; new search results
require visual/license review before they can be added here.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'data' / 'species_only' / 'captive'
MANIFEST = ROOT / 'data' / 'captive_species_manifest.json'
TAXON_ID = 29927
RETAINED_PHOTO_IDS = {
    430706442, 428746501, 428746493, 428746517,
    403358123, 403358245, 315809936, 315809873,
    306802511, 258690119, 258690133, 257157158,
    108982193, 33558128, 33558140, 33558158,
}
MANUAL_EXCLUSIONS = {
    306802531: 'Museum text/interpretation panel, not an animal photograph.',
    35242464: 'Outdoor field-like scene despite captive flag; excluded to honor captive-first selection.',
}
LICENSES = {
    'cc0': ('CC0-1.0', 'https://creativecommons.org/publicdomain/zero/1.0/'),
    'cc-by': ('CC-BY-4.0', 'https://creativecommons.org/licenses/by/4.0/'),
    'cc-by-sa': ('CC-BY-SA-4.0', 'https://creativecommons.org/licenses/by-sa/4.0/'),
}


def get_json(url: str) -> dict:
    request = Request(url, headers={'User-Agent': 'HogMorphStudio/1.0 (licensed reference curation)'})
    with urlopen(request, timeout=45) as response:
        return json.load(response)


def fetch_image(url: str, target: Path) -> tuple[int, int, str, int]:
    image_url = url.replace('/square.', '/medium.')
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            request = Request(image_url, headers={'User-Agent': 'HogMorphStudio/1.0 (licensed reference curation)'})
            with urlopen(request, timeout=60) as response:
                payload = response.read()
            image = Image.open(BytesIO(payload))
            image.load()
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.save(target, format='JPEG', quality=92, optimize=True)
            data = target.read_bytes()
            return image.width, image.height, hashlib.sha256(data).hexdigest(), len(data)
        except Exception as error:  # network hiccups are retried; schema/license failures are not
            last_error = error
            if attempt < 3:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'Could not fetch photo from {image_url}: {last_error}')


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    query = {
        'taxon_id': TAXON_ID,
        'captive': 'true',
        'photo_license': 'cc0,cc-by,cc-by-sa',
        'per_page': 200,
        'order': 'desc',
        'order_by': 'created_at',
    }
    api_url = 'https://api.inaturalist.org/v1/observations?' + urlencode(query)
    results = get_json(api_url)
    observations = {int(row['id']): row for row in results.get('results', [])}
    found: dict[int, tuple[dict, dict]] = {}
    licensed_photo_ids: set[int] = set()
    for observation in observations.values():
        if observation.get('taxon', {}).get('id') != TAXON_ID or observation.get('captive') is not True:
            continue
        for photo in observation.get('photos', []):
            photo_id = int(photo['id'])
            if photo.get('license_code') in LICENSES:
                licensed_photo_ids.add(photo_id)
            if photo_id in RETAINED_PHOTO_IDS:
                found[photo_id] = (observation, photo)

    missing = RETAINED_PHOTO_IDS - found.keys()
    if missing:
        raise RuntimeError(f'Reviewed photos absent from the current licensed/captive query: {sorted(missing)}')

    records = []
    for photo_id in sorted(RETAINED_PHOTO_IDS):
        observation, photo = found[photo_id]
        license_code = photo['license_code']
        license_name, license_url = LICENSES[license_code]
        filename = f'inat-captive-{photo_id}.jpg'
        target = DESTINATION / filename
        width, height, digest, size = fetch_image(photo['url'], target)
        records.append({
            'id': f'inat-captive-{photo_id}',
            'file': f'data/species_only/captive/{filename}',
            'sha256': digest,
            'bytes': size,
            'width': width,
            'height': height,
            'taxon_id': TAXON_ID,
            'taxon_name': observation.get('taxon', {}).get('name'),
            'quality_grade': observation.get('quality_grade'),
            'captive': True,
            'scope': 'captive_species_only_reference',
            'eligible_for_morph_training': False,
            'photo_id': photo_id,
            'observation_id': int(observation['id']),
            'observation_group': f"inat-observation-{observation['id']}",
            'individual_id': None,
            'subject_identity_verified': False,
            'observed_on': observation.get('observed_on'),
            'observer_login': observation.get('user', {}).get('login'),
            'attribution': photo.get('attribution'),
            'photo_page': f"https://www.inaturalist.org/photos/{photo_id}",
            'observation_page': f"https://www.inaturalist.org/observations/{observation['id']}",
            'download_url': photo['url'].replace('/square.', '/medium.'),
            'license_code': license_code,
            'license': license_name,
            'license_url': license_url,
            'metadata_stripped': True,
            'modifications': 'Used the iNaturalist medium-sized derivative; applied EXIF orientation, converted to JPEG, and removed embedded metadata.',
            'morph_labels': [],
            'genotype_evidence': None,
        })

    retained_observations = {record['observation_id'] for record in records}
    retained_codes = {}
    for record in records:
        retained_codes[record['license_code']] = retained_codes.get(record['license_code'], 0) + 1
    manifest = {
        'schema_version': 1,
        'source': 'iNaturalist Observations API + iNaturalist Open Data S3',
        'taxon_id': TAXON_ID,
        'taxon_name': 'Heterodon nasicus',
        'scope': 'species_only',
        'subscope': 'captive_unlabeled_reference_only',
        'morph_training_eligible': False,
        'selection_date': date.today().isoformat(),
        'query_url': api_url,
        'query_results_observations': int(results.get('total_results', 0)),
        'query_results_licensed_photos': len(licensed_photo_ids),
        'retained_photos': len(records),
        'retained_observations': len(retained_observations),
        'identity_verified_animals': 0,
        'morph_labeled_photos': 0,
        'training_eligible_photos': 0,
        'license_counts': retained_codes,
        'manual_exclusions': MANUAL_EXCLUSIONS,
        'selection_note': 'All records are marked captive by iNaturalist and licensed CC0/CC BY/CC BY-SA. Photos are species-only references; observer captivity flags do not establish breeder provenance or morph labels. Observation IDs group photos only for review and are not verified animal IDs.',
        'photos': records,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    retained_files = {Path(record['file']).name for record in records}
    for old_file in DESTINATION.glob('inat-captive-*.jpg'):
        if old_file.name not in retained_files:
            old_file.unlink()
    print(f"Saved {len(records)} licensed captive species-only references from {len(retained_observations)} observations to {MANIFEST}")


if __name__ == '__main__':
    main()

# Incoming photo batch audit

**Batch:** a user-supplied local folder, inventoried 2026-09-29. The source folder was not modified. Original media and the detailed image-indexed review remain outside the project and outside the local web server.

## Inventory and visual screen

| Measure | Count | Meaning |
| --- | ---: | --- |
| Files in the top-level folder | 301 | 152 `.jpg`, 76 extensionless images, 53 `.heic`, 19 `.png`, and 1 rejected `.txt` file |
| Decodable images | 300 | The extensionless image files were identified from their contents |
| Visual candidates for captive Western Hognose | 207 | Visual review only; not a unique-snake or rights count |
| Uncertain / possibly another species or partial image | 16 | Quarantined from the candidate set and held out pending human review |
| Confirmed non-target images | 77 | Excluded from private previews, contact sheets, and review exports |
| Exact duplicate groups | 2 | One group overlaps the uncertain set and one overlaps the candidate set |
| Candidate images with distinct exact file hashes | 206 | The candidate group includes one exact duplicate |
| Candidate near-duplicate pairs | 5 | Non-exact perceptual-hash distance 1–10; four look like same-scene repeats, one needs identity review |
| Additional same-scene crop pair | 1 | Indices 206/214 were visually matched despite a large dHash distance |
| Tentative candidate scene clusters | 201 | Deduplicates the exact pair and five visually reviewed same-scene pairs; this is not a unique-snake count |

The near-duplicate screen found five non-exact candidate pairs. Pairs 013/081, 057/211, 169/264, and 204/205 appear to show the same individual in the same enclosure across different frames or crops. Pair 115/121 includes a multi-snake frame and remains unresolved. The candidate set also has one exact byte-duplicate pair (198/290) and one manually matched scene/crop pair (206/214) that dHash did not catch. The review sheet marks all seven candidate pairs and also the uncertain exact-duplicate pair (184/189). Related photos should stay in the same data split. Watermarks, overlays, and screenshots appear in part of the batch. A watermark is not a rights record.

The image review is only a visual species screen. It did not assign morph labels, infer genotype, verify individual snake IDs, or establish photo permission. Some source images include GPS metadata; the private review previews were re-encoded without EXIF metadata. The original files remain untouched.

## Source and text metadata check

An English-only OCR scan found no exact breeder morph-name strings. Chinese text recognition was not available in the local OCR runtime, so embedded Chinese captions remain unreviewed. A read-only EXIF scan found no usable artist/copyright/source fields; 24 originals contain GPS metadata. This does not establish ownership or permission. Only metadata-stripped previews are used for review.

## Training readiness

**Eligible morph-training images: 0.** The batch has no accompanying specimen-ID, morph-label, breeding/genetic evidence, reviewer, or media-rights manifest. The photo count exceeds 100, but the verified morph-labeled corpus target is not met: the `207` are visual candidates, not labeled training examples.

Before any image becomes training eligible, the review needs, per photo: its source and rights evidence, explicit permission for training and evaluation, individual snake ID, confirmed visible-trait labels with evidence, reviewer, and explicit negative labels only where supported. Demo display and public-web permission remain separate fields. Duplicate photos must stay grouped under the same individual for model splitting.

## Local review artifacts

- Active candidate previews and contact sheets: `~/Library/Application Support/HogMorphStudio/incoming-review/previews/` and `~/Library/Application Support/HogMorphStudio/incoming-review/sheets/candidates/`. Uncertain photos are kept in a separate quarantine sheet. Confirmed non-target previews were removed from staging; source originals remain in the supplied folder.
- Fillable per-photo review sheet: `~/Library/Application Support/HogMorphStudio/incoming-review/review_manifest.csv`
- Rebuild the inventory and metadata-stripped contact sheets with `scripts/stage_incoming.py` and the bundled Pillow Python runtime. By default it writes under the current macOS user's Application Support directory; the script rejects output paths overlapping the source folder, project tree, or local web-server root.
- Rebuild the blank review sheet with `python3 scripts/export_incoming_review_csv.py "$HOME/Library/Application Support/HogMorphStudio/incoming-review/reviewed_inventory.json" --output "$HOME/Library/Application Support/HogMorphStudio/incoming-review/review_manifest.csv"`.
- `data/incoming_summary.json` contains counts only; it does not bundle or serve the supplied photos.

Keep the rights columns blank until the rights holder and permission scope are confirmed. `image_rights` accepts `owner_permission`, `cc0`, `cc_by_4_0`, or `public_domain` in the training validator; the rights evidence must explicitly include training and evaluation. `source_scope` should be `captive_morph` only for confirmed captive morph photos. Use canonical labels such as `albino:expressed` and `sable:expressed`; a combination nickname such as Sunburst should be decomposed into its component labels. Never mark carrier status from a photo. The `potential_duplicate_group` column is a similarity warning, not an asserted individual ID; confirm identity before assigning groups or splitting data. This CSV is a review worksheet, not a training manifest; records still need to pass `scripts/prepare_training_manifest.py` before training.

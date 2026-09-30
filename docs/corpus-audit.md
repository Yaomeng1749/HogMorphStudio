# Licensed species-only reference subsets

## Wild observations

**Selection date:** 2026-09-29 (America/Los_Angeles). The 16 retained iNaturalist photographs are a deliberately small wild/species-only set, selected from 16 distinct Research Grade observations for the exact species `Heterodon nasicus` (taxon 29927). Selection preferred CC0 photographs, then added three CC BY photographs. There is at most one retained photo per observation. The collection is **not** a 100-photo morph corpus.

`data/species_manifest.json` records the original photo ID, observation ID, source URL, download URL, license URL, observer, attribution, dimensions, bytes, and SHA-256. All 16 copied files were checked against those SHA-256 values when imported. License mix: **13 CC0; 3 CC BY**. Source images remain unchanged.

Wild sightings have neither breeder-confirmed morph tags nor proof that a snake lacks a recessive or other genetic variant. All records have `scope=species_only`, empty `morph_labels`, and `eligible_for_morph_training=false`. The gallery renders them separately and the analyzer does not read this manifest for image comparison. No wild photo is used as a morph-class negative.

The complete discovery set was larger, but additional field photos add limited value to this goal. The remaining gap is owner-authorized, individually identified captive morph photos with label evidence and review. See `docs/partner-request.md` for an unsent contribution request.

## Captive, morph-unlabeled observations

**Selection date:** 2026-09-30. A fresh iNaturalist API query returned 11 captive-marked observations and 18 CC0/CC BY/CC BY-SA photo assets. Visual review retained 16 animal photos from 10 observation records and excluded one text panel and one outdoor field-like photograph. The retained images are in [`data/captive_species_manifest.json`](../data/captive_species_manifest.json), separately displayed from the wild references. The query's `captive=true` flag and a source taxon identification do not prove breeder provenance, unique animal identity, or any morph/genotype label. No observation had a verified morph label, so all 16 remain species-only references and all are denied morph training eligibility.

The 16 files use the iNaturalist medium-sized derivatives: EXIF orientation is applied, each is converted to JPEG, and embedded metadata is removed. License mix is 4 CC0 and 12 CC BY 4.0. Per-photo source/observation URLs, attribution, license, modification note, output dimensions, and SHA-256 are in the manifest and visible in the gallery. Photos from one observation share a review group; cross-observation animal identity is unknown. These images support captive-species visual context only; they do not count toward the 100 individually verified morph-photo target.

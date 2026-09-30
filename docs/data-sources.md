# Public-data search notes

**Checked 2026-09-30.** A targeted search did not surface a directly usable, openly licensed Western Hognose morph dataset with specimen-level, reliable morph/genotype ground truth. Public snake detection sets classify species or broad snake objects, not western hognose morphs. We found one CC0 captive photo whose uploader reports a pet-store Anaconda label; it remains a single provisional source-claim candidate, not verified ground truth or a training example.

## Possible supporting source: iNaturalist

The iNaturalist taxon observations can help with species-level visual reference, but its community identifications are species observations, not breeder-confirmed morph labels. The initial broad API count conflated observation licenses and photo licenses, so it is not used as an eligibility number. The actual retained set has 16 photos from 16 distinct Research Grade observations, each with an individually checked CC0 or CC BY photo license. See [`docs/corpus-audit.md`](corpus-audit.md) and [`data/species_manifest.json`](../data/species_manifest.json).

- [iNaturalist taxon page](https://www.inaturalist.org/taxa/29927-Heterodon-nasicus)
- [iNaturalist Search URL and photo-license filters](https://help.inaturalist.org/en/support/solutions/articles/151000170738)
- [iNaturalist guidance for research image downloads](https://help.inaturalist.org/en/support/solutions/articles/151000223300-how-i-download-inaturalist-photos-to-use-for-research-)

The iNaturalist help guidance says to follow the license attached to each photo. Keep the observation/photo URL, observer credit, license, and attribution with every retained image. Do not assume that the observation license and its media license are identical.

On 2026-09-30, `GET https://api.inaturalist.org/v1/observations?taxon_id=29927&captive=true&photo_license=cc0,cc-by,cc-by-sa&per_page=200` returned 11 observations. In lowercased observation descriptions and `species_guess` fields, the search terms `albino`, `anaconda`, `conda`, `sable`, `arctic`, `axanthic`, `lavender`, `toffee`, and standalone `het` had zero matches. `het` means the standalone morph abbreviation here; it is not counted inside the taxon name “Heterodon.” These records are not added to the morph corpus: a captive species observation without specimen-level trait evidence is still not a morph label.

A fresh API fetch confirmed those 11 observations contain 18 photos with per-photo CC0/CC BY/CC BY-SA license codes. Visual review retained 16 animal photos from 10 observations, excluding one museum information panel and one outdoor field-like image despite its `captive=true` flag. The retained image license mix is 4 CC0 and 12 CC BY; photos are shown in a separate captive species-only gallery with attribution and a notice that each iNaturalist medium-sized derivative was orientation-corrected, converted to JPEG, and stripped of embedded metadata. See [`data/captive_species_manifest.json`](../data/captive_species_manifest.json) and [`docs/corpus-audit.md`](corpus-audit.md). None has verified morph evidence or an individually confirmed snake ID, so none is eligible for morph training or counted toward the 100-photo morph target.

## Genetic and phenotype terminology

“White Wall” is retained as a visual descriptor rather than a genetic label. Reptifit's [Anaconda guide](https://www.reptifit.nl/en/collection) describes Anaconda as a pattern-affecting locus; the community [Hognose Wiki Anaconda entry](https://hognose.fandom.com/wiki/Anaconda) mentions white walls as an appearance associated with some Anacondas. The descriptor by itself does not establish Anaconda or any genotype.

## Morph-reference leads

- [Hognose Hub Genetics Lab](https://hognosehub.com/genetics-lab/guide) is a community-maintained morph/genetics reference that invites photo submissions; for example, the [Sunburst page](https://hognosehub.com/genetics-lab/sunburst) names Albino + Sable and credits a community photo. It is not a ready-to-train downloadable ML dataset. Its [Content Use Policy](https://hognosehub.com/legal/content-use) asks for prior written permission before using Hognose Hub's original materials in a training platform or published resource. Obtain photo permission from each rights holder; request Hub permission when reusing Hub-authored protected materials.
- [Reptifit's collection](https://www.reptifit.nl/en/collection) and [Solar Flare listing](https://www.reptifit.nl/en/available/western-hognose-snake-solar-flare/) document captive morph combinations, including Sable + Albino + Anaconda. These listings support partnership and label research only. The pages do not state that their displayed photos are licensed for reuse, so request permission from the photo rights holder before copying, training, or public display.
- [Wikimedia Commons: Western hognose at a pet store](https://commons.wikimedia.org/wiki/File:Western_hognose_at_a_pet_store.jpg) is declared CC0 1.0 on the file page. Its description says the pet-store label called the snake an Anaconda morph and names it Miss Piggy. This is a reported label, not breeder/genotype evidence; the image is included only as an attributed, metadata-stripped review/demo candidate and is not training eligible. Its exact rights and hashes are recorded in `data/reference_gallery.json`.
- Wikimedia Commons search for `Heterodon nasicus` and hognose morph terms also returned CC BY/CC BY-SA species and zoo files (including [Dawson's Heterodon nasicus](https://commons.wikimedia.org/wiki/File:Heterodon_nasicus.jpg) and [Micro Zoo de Saint-Malo](https://commons.wikimedia.org/wiki/File:Micro_Zoo_de_Saint_Malo_-_Heterodon_nasicus_01.jpg)). These pages do not document morph labels or unique animal identities, so they remain outside the morph corpus.
- [Hognose Wiki](https://hognose.fandom.com/wiki/Hognose_Wiki) describes community content as CC BY-SA, but confirm the license and attribution for each embedded image before reuse.
- Breeder marketplaces and forums often pair morph claims with images, but the seller's label is not automatically verified ground truth and a publicly viewable image is not automatically reusable.

## Recommendation

Use the currently supplied DOCX as a local visual reference only; its image-rights records are missing. Ask breeders/keepers to contribute images with explicit reuse permission and individual IDs, and have a knowledgeable reviewer confirm visible traits against breeding/genetic evidence. Keep species-level open data separate from pet morph records. Do not merge the two sources into a single training set.

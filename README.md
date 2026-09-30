<div align="center">
  <img src="assets/hero-natural-history.png" alt="AI-generated Western Hognose illustration; not specimen data" width="900">
  <h1>HogMorph Studio</h1>
  <p><strong>See the pattern. Respect the unknown.</strong></p>
  <p>A bilingual, local-first workbench for Western Hognose photo review, morph terminology, and evidence-aware dataset curation.</p>
  <p><a href="README.zh-CN.md">简体中文</a> · <strong>English</strong></p>
  <p><code>TypeScript</code> · <code>Python</code> · <code>PyTorch</code> · <code>Local-first</code></p>
</div>

## Demo

<p align="center">
  <a href="docs/assets/hogmorph-studio-demo.mp4">
    <img src="docs/assets/hogmorph-studio-demo-preview.gif" alt="HogMorph Studio bilingual interface and local curation workflow demo" width="900">
  </a>
  <br><sub>Click the preview for the 27-second MP4. The staged image is an AI-generated UI illustration, never biological data.</sub>
</p>

The recording tours the bilingual interface, implemented research pipeline, measured runtime comparison, and local review workflow. It does **not** show a trained morph classifier. The live photo screen is still a color/layout similarity baseline; its percentages are not softmax confidence, genotype probabilities, or proof of a morph.

## What it does

- **Review a photo locally.** The browser keeps selected photos in memory. A clone without an authorized morph reference set abstains and returns no similarity score.
- **Track evidence before labels.** Review drafts capture source URL, specimen ID, image rights, genotype evidence, annotator, reviewer, and uncertainty before JSON export.
- **Keep names and traits separate.** Trade names can map to atomic traits (for example, the ontology represents Sunburst as Albino + Sable). White Wall is recorded as an appearance descriptor, not a gene.
- **Reproduce and measure the research path.** Python/PyTorch implementations cover the historical CNN, FPPA denoising, Butterworth filtering, and a gated MobileNetV3-Small multilabel trainer with individual-grouped evaluation.
- **Show uncertainty explicitly.** Unknown labels remain unknown; wild-type appearance is not treated as a proven genetic negative.

## Current evidence and limits

This is a working research prototype, not a validated genetic test. The MobileNet trainer is implemented but has **not** been trained: there are currently zero records that meet the combined requirements for verified morph labels, individual identity, training/evaluation rights, and independent evaluation. The project does not claim morph-classification accuracy.

The live browser baseline compares color histograms and a coarse spatial color grid with the original **21-photo local course archive** when that archive is available on the developer's machine. It measures nearest-image color/layout overlap and sample support only. Its background, crop, and lighting sensitivity make it unsuitable for genotype or carrier-status decisions. The archive is not distributed in this repository. A clean clone remains usable for curation and deliberately shows no comparison score until a rights-cleared reference set is supplied.

### Implemented model work

| Work | Result | What it establishes |
| --- | --- | --- |
| FPPA denoising on 21 course images with a fixed synthetic-noise protocol | Mean PSNR 22.3315 → 26.7765 dB; SSIM 0.5076 → 0.7598 | Image reconstruction only; not improved morph recognition |
| Legacy CNN vs. MobileNetV3-Small, batch 1, Apple M5, random weights | CNN: 6.027 ms CPU / 1.317 ms MPS median; MobileNet: 16.795 ms CPU / 6.705 ms MPS median | Architecture/runtime comparison only; MobileNet was smaller but slower in this setup |
| MobileNetV3-Small multilabel training path | Implemented: masked BCE-with-logits, identity-level splits, per-class support gates, and per-individual bootstrap intervals | No accuracy claim; the training gate stays closed until the eligible dataset exists |

Full protocols, p95 timings, hardware/software details, support rules, and limitations are in [model architecture](docs/model-architecture.md), [experiment plan](docs/experiment-plan.md), and [Python reproduction notes](docs/python-model-port.md).

## Run locally

Requirements: Node.js with npm, Python 3, and a browser. No API key or hosted inference service is required.

```bash
npm ci
npm run build
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/>. The interface switches between English and Chinese. On a clean clone, the analyzer will abstain until you install a reviewed, authorized morph reference archive. Uploaded review drafts stay in the browser until you explicitly export them.

Optional Python research environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-ml.txt
python scripts/python_reproduction.py --help
```

The supervised trainer has a fail-closed data gate; see the [model data requirements](docs/model-architecture.md) before preparing a manifest. It will not train from visually screened but unverified photos.

## Dataset status and rights

There are **not yet 100 eligible morph-labeled images**. The user-supplied image batch was screened for likely species, but visual candidates are not genotype labels, unique-animal identities, or rights clearance. Training eligibility is currently zero. The needed minimum is 100 authorized, reviewed photos from 39 or more identifiable snakes, with class-specific positives and explicit negatives sufficient for identity-separated train, validation, and test sets.

Breeders with individually documented, captive animals can review the [contribution request](docs/partner-request.md) and [source lead list](docs/partner-shortlist.md). Training/evaluation permission and public photo display or redistribution are requested as separate scopes; the code's MIT license does not apply to contributed photographs.

Publicly viewable Instagram, MorphMarket, and wiki images are not automatically reusable. No Instagram or MorphMarket images were copied into the repository. The supplied course workbook, its 21 photos, and images embedded in the supplied genetics guide have unrecorded reuse rights and are not distributed. Licensed iNaturalist references are retained only as attributed, species-only examples; they do not count as morph examples or genetic negatives. See [asset rights](ASSET_RIGHTS.md), [dataset source audit](docs/dataset-source-audit-2026-09-30.md), and the [incoming photo audit](docs/incoming-audit.md).

`LICENSE-CODE` covers project-authored software only. It does not change third-party photo licenses or grant rights in source documents.

## Project map

- `src/` — bilingual TypeScript web interface, curation workflow, and local similarity baseline
- `scripts/` — Python model reproduction, manifest validation, dataset checks, and evaluation pipeline
- `data/ontology.json` — morph-name and atomic-trait ontology, including uncertainty notes
- `data/species_manifest.json`, `data/captive_species_manifest.json` — source and license records for species-only reference photos
- `docs/` — architecture, migration, evaluation, corpus, and source-audit notes

## License

Project-authored code: [MIT](LICENSE-CODE). Photographs and source materials retain their own terms; consult [ASSET_RIGHTS.md](ASSET_RIGHTS.md) before reuse.

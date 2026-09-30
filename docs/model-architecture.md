# Model baseline / 模型基线

> Current demo update (2026-09-30): the live analyzer uses a configured pretrained vision-language model and 18 authorized course-photo references. The owner confirmed all 21 historical course labels (White Wall removed), and requested deletion of 207 incoming candidates; 16 uncertain images remain privately quarantined. The supervised CNN/MobileNet path and prior audit findings below remain research records, not the live inference architecture. See [multimodal demo](multimodal-demo.md) for current behavior.

## Implemented Python reproduction

The 2024 MATLAB model shape and paper-specified FPPA denoising method have been ported to Python 3/PyTorch and NumPy/SciPy. The old script’s data-loading and evaluation path remains non-reproducible: it references a missing workbook and undefined test set, and `denoiseplus.m` is empty. The port makes the architecture and denoiser executable; it does not claim to reproduce MATLAB weights or training results. Full commands and measured results are in [`python-model-port.md`](python-model-port.md).

On 21 local course images with deterministic synthetic Gaussian noise, FPPA improved mean PSNR by 4.4450 dB (22.3315 to 26.7765) and SSIM by 0.2522 (0.5076 to 0.7598). This evaluates denoising against the original clean image only. The preprocessing effect on morph recognition is unknown.

The source workbook contains 101 named rows, but only 21 rows have matching images and historical annotations; the remaining 80 are blank placeholders. Those annotations have not been verified against individual IDs, a label codebook, breeder evidence, or image training/evaluation permissions. The `White Wall` column is an appearance descriptor and is excluded from genetic trait training. The 21 images were used as pixel inputs only for the FPPA experiment. See the [course workbook audit](course-workbook-audit.md); no morph-classifier training or evaluation has been performed.

**Task:** multi-label *visible phenotype* screening for Western hognose photos. Each independent output corresponds to a canonical expressed trait/state such as `albino:expressed`, `anaconda:heterozygous`, or `anaconda:homozygous`. The UI may derive known combination names from component scores, but an image result remains a hypothesis pending review.

## Why MobileNetV3-Small first

The project has whole-animal photos and several simultaneous morphs. [MobileNetV3-Small](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.mobilenet_v3_small.html) is an image-classification architecture; replacing its final layer with one output per trait permits a baseline without bounding boxes. YOLO is a detector; it is useful if box annotations and snake localization are needed. It does not solve sparse morph labels.

We measured both architectures on Apple M5 with batch size one, 224×224 RGB input, 10 warmups, 50 timed runs, and random weights. The legacy CNN (18 output logits) had 6,448,786 parameters and a 25,803,992-byte serialized state; its median/p95 was 6.027/7.000 ms on CPU and 1.317/1.869 ms on MPS. MobileNetV3-Small (default 1,000 output logits) had 2,542,856 parameters and a 10,301,335-byte state; its median/p95 was 16.795/17.330 ms on CPU and 6.705/8.642 ms on MPS. Thus, on this device/runtime, MobileNet was smaller but slower. This random-weight benchmark does not establish trained-model performance or generalize to other hardware.

The loss is PyTorch [`BCEWithLogitsLoss`](https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html), masked for unknown labels. The model uses independent sigmoid outputs. Softmax would incorrectly force mutually exclusive classes: Sunburst genuinely contains both Sable and Albino. A blank workbook cell is unknown, never a negative training target. Carrier states are not trained from photos.

## Data gate

`scripts/prepare_training_manifest.py` accepts only local images with individual ID, source URL, image-rights status, rights evidence where required, attribution, reviewer, reviewed status, morph evidence and at least one positive explicit 0/1 label. It rejects duplicate image bytes. Licensed species photos without morph evidence are useful for a snake detector or visual pretraining, but not as morph ground truth.

Example input JSONL record (paths resolve relative to the input manifest):

```json
{"id":"snake-001-view-1","image":"photos/001.jpg","individual_id":"snake-001","source_scope":"captive_morph","source_url":"https://example.org/record/001","image_rights":"owner_permission","rights_evidence_url":"https://example.org/permission/001","rights_reviewed_by":"Rights reviewer","rights_scopes":{"training":true,"evaluation":true,"hackathon_demo":false,"public_web":false},"attribution":"Owner name","genotype_evidence":"breeder_record","evidence_url":"https://example.org/lineage/001","claim_scope":"genotype","review_status":"reviewed","reviewer":"Morph reviewer","aliases":["sunburst"],"labels":{"anaconda:heterozygous":0}}
```

Allowed `image_rights`: `owner_permission`, `cc0`, `cc_by_4_0`, `public_domain`; each needs a `rights_evidence_url` documenting that status and a named `rights_reviewed_by` reviewer. `rights_scopes` must explicitly record four booleans: `training`, `evaluation`, `hackathon_demo`, and `public_web`. The training gate requires the first two to be true; the latter two are retained separately so training permission never becomes display permission. These declarations require human verification against the original grant or photo license; a string URL alone cannot prove permission. Allowed `genotype_evidence`: `breeder_record`, `genetic_test`, `expert_phenotype_review`; the last requires `claim_scope=phenotype`. The alias expands positive components but does not manufacture negatives. An unlisted class, conflicting same-locus states, missing evidence, or absent image is rejected.

`source_scope` must explicitly be `captive_morph`. The 16 known field-reference images are denied by file SHA-256 even if copied under another name and supplied with invented metadata. The remaining rights and genetics evidence still require human review; this gate cannot verify a newly supplied photograph's ownership or ancestry by itself.

```bash
python3 scripts/prepare_training_manifest.py data/reviewed_records.jsonl \
  --output .runtime/eligible.jsonl --report .runtime/gate-report.json
python3 scripts/train_multilabel.py .runtime/eligible.jsonl \
  --output .runtime/model-run --epochs 12
```

Training refuses fewer than **100 eligible images** and checks the identity-level split capacity before importing PyTorch. Although the broad data floor remains 30 individuals, that count cannot support the class gate: with the seeded 70/15/15 partition sizes, validation has only 4 and test 5 individuals. Since each evaluated class needs at least 3 positive **and** 3 explicit-negative individuals in both validation and test, the first total whose partition capacities can meet those constraints is **39 distinct individuals** (27/6/6). This is a mathematical capacity floor, not a sufficient sample-size recommendation.

The trainer uses deterministic, seed-controlled whole-individual split optimization. It preserves 70/15/15 partition sizes, first maximizes how many classes satisfy the support gate, then maximizes capped support toward each split's minimum. It reports per-class positive/explicit-negative counts and global feasibility before importing PyTorch; if support remains inadequate, it exits with the diagnostics. Contradictory explicit labels for the same individual and class are rejected rather than split across images. Each trained class still needs at least 5 positive and 5 explicit-negative individuals in training, and 3 of each in validation and test; unsupported classes are listed as omitted. These minima are a prototype gate, not evidence of broad generalization. Thresholds are selected using validation data, then evaluated once on test data. The saved `metrics.json` gives split sizes, per-class precision, recall, F1, average precision (AP), macro-F1, and 95% percentile intervals from test-individual bootstrap resampling. AP is a ranked precision-recall summary and is not labeled trapezoidal PR-AUC. Per-class interval denominators are metric-specific: only resamples where that metric is defined count, and the report records valid counts. Macro-F1 uses a fixed complete-class estimand and retains only resamples where every evaluated class has both positive and negative examples; its valid count is also reported. These conditional percentile intervals are descriptive and can be unstable with few test individuals; they do not establish population-level generalization. Raw sigmoid output is an uncalibrated score, not a trustworthy genotype probability. No metrics are supplied until actual eligible data and a completed run exist.

## Open-set review

Unknown or novel appearances should be flagged for manual review. Possible future triggers include low maximum score, disagreement among augmentations, or distance from the training embeddings; thresholds require validation against known and deliberately held-out morphs. An outlier is not automatically a new gene. Expansion requires source documentation, multiple independent animals and expert review, followed by a new ontology version and retraining.

# MATLAB to Python migration

## Language and runtime

The research/model pipeline is now Python 3, using PyTorch for neural networks and NumPy/SciPy/Pillow for image processing. The browser interface has also moved from untyped JavaScript to TypeScript modules, compiled with `npm run build` into the static `build/` directory. The Python model is not currently wired into the photo-upload page: that page still runs its explicitly labeled visual-similarity baseline in the browser.

## MATLAB-to-Python map

| 2024 MATLAB stage | Current Python implementation | Migration decision |
| --- | --- | --- |
| `imageDatastore` + workbook labels | `prepare_training_manifest.py` | Replaced implicit spreadsheet loading with a reviewed, provenance-aware manifest. Blank values remain unknown. |
| `augmentImages.m` | training transforms in `train_multilabel.py` | Augmentation occurs only on the identity-grouped training split. The old 90-degree rotation is not copied because orientation changes can alter visible pattern cues. |
| 3-convolution, 224px CNN | `LegacyHognoseCNN` in `python_reproduction.py` | Architecture shape and multilabel logits are reproduced. `masked_bce_with_logits` prevents unknown labels from becoming negatives. |
| `trainNetwork` with Adam | `train_multilabel.py` | Replaced with a gated MobileNetV3-Small baseline, AdamW, masked BCE, and train/validation/test splits grouped by snake identity. The historical CNN remains available for architecture/runtime comparisons. |
| `predict` and percentage table | validation threshold selection and per-class test metrics in `train_multilabel.py` | Uses independent sigmoid outputs for multilabel traits. Outputs are uncalibrated scores; the UI does not present them as genetic probabilities. |
| `save('CNN_snake.mat', ...)` | `model.pt` plus `metrics.json` | Saves a PyTorch state dict, class order, thresholds, architecture, image size, and evaluation report after a real gated training run. |
| `denoiseplus.m` | `fppa_tv_denoise` and optional `butterworth_lowpass` | `denoiseplus.m` was empty, so no behavior could be translated from it. FPPA is implemented from the supplied paper and measured separately. |

## Deliberate fixes to the old workflow

The MATLAB Live Script's embedded output reports a label-table path error. It also calls an undefined `testData`, while `augmentImages.m` invokes `denoiseplus(imds)` rather than passing its current image. It augments before defining any independent split. Those failures and leakage risks are not carried forward. The Python trainer validates evidence and permissions first, groups all images from one snake into one split, and augments only the training partition.

The original folder contains no exported `CNN_snake.mat` model weights. Weight conversion is therefore not implemented: there is no trained MATLAB checkpoint whose layer tensors or learned `zerocenter` mean can be verified. A Python training run estimates its own preprocessing through the declared transform instead of inventing those missing values.

## Current execution boundary

The Python training and held-out evaluation code is implemented, but it must refuse to run on the current collection: there are zero records with verified morph labels, individual IDs, and both training and evaluation rights. The local visual matcher remains a separate TypeScript baseline. Do not describe either path as a validated genetic classifier until a real training run and independent test report exist.

## Current application stack

| Area | Language and runtime | Responsibility |
| --- | --- | --- |
| Browser UI | TypeScript 7, HTML, CSS | Bilingual archive, image review, ontology/reference views, and local visual-similarity demo. Compiled assets are checked into `build/` so the static preview works without a frontend development server. |
| Model research | Python 3, PyTorch, NumPy, SciPy, Pillow | CNN reproduction, image-processing experiments, gated MobileNetV3-Small training and grouped evaluation. |

Build the TypeScript interface with `npm install && npm run build`. The existing Python scripts remain the reproducible model and dataset tools; no Python API service is required for the current local demo.

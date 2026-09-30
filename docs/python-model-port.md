# Python port of the core 2024 MATLAB image methods

This is an executable Python 3 port of the model shape in `TrainCNN_multiple_Lables.mlx` and of the FPPA method defined in the supplied 2024 `FPPAforDenoising.pdf`. The provided `denoiseplus.m` is a zero-byte file; there was no MATLAB implementation to translate there. This port implements the paper's stated algorithm directly.

## What is implemented

- `LegacyHognoseCNN` reproduces the 224x224 RGB input, three same-padded 3x3 convolutions (16, 32, 64 channels), batch normalization, ReLU and 2x max pooling, a 128-unit ReLU layer, dropout 0.5, and one output per label. It returns logits: sigmoid is applied only for inference display, while training uses masked `BCEWithLogitsLoss`. Unknown cells are masked from the loss, rather than treated as negative labels.
- `fppa_tv_denoise` implements the paper's anisotropic ROF objective `0.5 ||u-v||_2^2 + mu ||Bu||_1`, initialization `y0=Bv`, clipped fixed-point dual iteration, and final `u=v-step B.T y`. Its forward differences have zero first row/column, and the adjoint follows the paper's boundary equations. RGB planes are processed independently to retain color.
- `butterworth_lowpass` is a separate optional per-channel frequency filter. It is not silently chained with FPPA or the CNN. Neither filter's effect on morph classification has been evaluated.
- `experiment` and `benchmark` are measurement commands only. There is intentionally no training command in this port.

Install the declared runtime dependencies and run checks:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-ml.txt
PYTHONPATH=scripts python -m unittest scripts/test_python_reproduction.py -v
```

## Reproduction commands

Supply a local directory of images; images and model weights are not included in this repository. For the supplied course images:

```bash
python scripts/python_reproduction.py experiment \
  "/path/to/猪鼻蛇大作业/image_data" --output /tmp/hogmorph-fppa.json
python scripts/python_reproduction.py benchmark --device cpu --warmup 10 --repeats 50
python scripts/python_reproduction.py benchmark --device mps --warmup 10 --repeats 50
```

The experiment resizes to 224x224 RGB, adds deterministic clipped Gaussian noise (`seed=2024`, standard deviation `20/255`), then compares noisy and FPPA outputs against the clean resized image. PSNR uses data range 1. SSIM is the standard luminance/contrast/structure expression with a Gaussian window (`sigma=1.5`, data range 1), averaged across RGB channels and images. Defaults are `mu=0.08`, `step=0.24` (paper requires `< 1/4`) and 80 iterations. Parameters are fixed for this report, not tuned on a held-out validation set.

## Measurements from the supplied local images

The 21 local `image_data/figure1.png` through `figure21.png` files were used in place. No photos or weights were copied into the repository. With the defaults above, the mean scores were:

| Input | PSNR (dB) | SSIM |
| --- | ---: | ---: |
| Synthetic noisy | 22.3315 | 0.5076 |
| FPPA denoised | 26.7765 | 0.7598 |

These results measure reconstruction against the original images under this synthetic noise protocol only. They are not evidence that either preprocessing step improves morph recognition.

The following batch-1 forward-pass timings were measured on an Apple M5 with PyTorch 2.14.0 / torchvision 0.29.0, 224x224 RGB inputs, 10 warmups and 50 timed runs, with randomly initialized weights. Timing includes device synchronization for MPS. State-dict size is PyTorch's serialized, uncompressed parameter and buffer state.

| Model | Parameters | State dict | CPU median / p95 | MPS median / p95 |
| --- | ---: | ---: | ---: | ---: |
| Legacy 3-convolution CNN, 18 logits | 6,448,786 | 25,803,992 bytes | 6.027 / 7.000 ms | 1.317 / 1.869 ms |
| MobileNetV3-Small, default 1,000 logits | 2,542,856 | 10,301,335 bytes | 16.795 / 17.330 ms | 6.705 / 8.642 ms |

These are local architecture/inference measurements, not trained-model comparisons. MobileNetV3-Small is smaller here but slower on this machine and runtime. Neither model's accuracy was evaluated.

## Data and claims boundary

The locally supplied workbook has 101 named rows but only 21 matching image rows with annotations; the other 80 rows are blank placeholders. Its label semantics, specimen IDs, split independence, and the photos' training/evaluation rights have not been verified. The `White Wall` column is a visible descriptor, not a genetic locus, and is excluded from trait training. Therefore **the supervised morph-classifier training gate remains closed**: this work did not train, validate, or test a morph classifier and reports no morph accuracy, F1, or genotype probability. The FPPA experiment uses the 21 images as pixel inputs only; it does not use their workbook labels. See the [course workbook audit](course-workbook-audit.md). Future training still requires the existing reviewed-manifest gates and independently reviewed labels and permissions.

The benchmark's 18-output legacy head demonstrates the declared class-output shape only; it is not inferred as a verified workbook class count. MATLAB's `zerocenter` behavior depended on its training-set mean image; the port does not invent that statistic. A future supervised run must estimate and persist its training-only normalization values and use them unchanged at inference. Existing MATLAB weights are not loaded or converted by this script.

#!/usr/bin/env python3
"""Python port of the core 2024 MATLAB image-model methods.

This module ports the CNN architecture and the FPPA total-variation denoiser.
It deliberately provides no training command: the supplied photo labels and
image rights have not been reviewed for supervised morph classification.
"""

from __future__ import annotations

import argparse
import io
import json
import statistics
import time
from pathlib import Path

import numpy as np
from PIL import Image


try:
    import torch
    from torch import nn
except ImportError:  # Keep denoising usable when only image dependencies are installed.
    torch = None
    nn = None


def forward_difference(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply the paper's B operator; leading row/column differences are zero."""
    image = np.asarray(image, dtype=np.float64)
    if image.ndim not in (2, 3):
        raise ValueError("Expected HxW grayscale or HxWxC image")
    vertical = np.zeros_like(image)
    horizontal = np.zeros_like(image)
    vertical[1:, ...] = image[1:, ...] - image[:-1, ...]
    horizontal[:, 1:, ...] = image[:, 1:, ...] - image[:, :-1, ...]
    return vertical, horizontal


def adjoint_difference(vertical: np.ndarray, horizontal: np.ndarray) -> np.ndarray:
    """Apply B.T using the boundary terms derived in FPPAforDenoising.pdf."""
    vertical = np.asarray(vertical, dtype=np.float64)
    horizontal = np.asarray(horizontal, dtype=np.float64)
    if vertical.shape != horizontal.shape or vertical.ndim not in (2, 3):
        raise ValueError("Difference arrays must have the same HxW or HxWxC shape")
    result = np.zeros_like(vertical)
    result[0, ...] -= vertical[1, ...] if vertical.shape[0] > 1 else 0
    if vertical.shape[0] > 2:
        result[1:-1, ...] += vertical[1:-1, ...] - vertical[2:, ...]
    if vertical.shape[0] > 1:
        result[-1, ...] += vertical[-1, ...]
    result[:, 0, ...] -= horizontal[:, 1, ...] if horizontal.shape[1] > 1 else 0
    if horizontal.shape[1] > 2:
        result[:, 1:-1, ...] += horizontal[:, 1:-1, ...] - horizontal[:, 2:, ...]
    if horizontal.shape[1] > 1:
        result[:, -1, ...] += horizontal[:, -1, ...]
    return result


def fppa_tv_denoise(image: np.ndarray, mu: float = 0.08,
                    step: float = 0.24, iterations: int = 80) -> np.ndarray:
    """Solve the anisotropic ROF model with the fixed-point proximity method.

    The paper's conditions are mu > 0 and step < 1/4. RGB channels are handled
    independently, preserving all three color channels throughout.
    """
    source = np.asarray(image, dtype=np.float64)
    if source.ndim not in (2, 3) or (source.ndim == 3 and source.shape[2] not in (1, 3, 4)):
        raise ValueError("Expected HxW grayscale or HxWxC image")
    if not np.isfinite(source).all():
        raise ValueError("Input image must contain finite values")
    if mu <= 0 or not 0 < step < 0.25 or iterations < 1:
        raise ValueError("Require mu > 0, 0 < step < 1/4, and iterations >= 1")

    b_v, b_h = forward_difference(source)
    y_v, y_h = b_v.copy(), b_h.copy()  # paper initialization y0 = Bv
    threshold = mu / step
    for _ in range(iterations):
        bt_y = adjoint_difference(y_v, y_h)
        bbt_v, bbt_h = forward_difference(bt_y)
        # (I - prox_(mu/step ||.||_1)) is projection onto the l-infinity ball.
        y_v = np.clip(b_v + y_v - step * bbt_v, -threshold, threshold)
        y_h = np.clip(b_h + y_h - step * bbt_h, -threshold, threshold)
    return source - step * adjoint_difference(y_v, y_h)


def butterworth_lowpass(image: np.ndarray, cutoff: float = 0.12,
                        order: int = 2) -> np.ndarray:
    """Optional per-channel Butterworth frequency low-pass, separate from FPPA."""
    from scipy.fft import fft2, fftfreq, ifft2

    source = np.asarray(image, dtype=np.float64)
    if source.ndim not in (2, 3) or (source.ndim == 3 and source.shape[2] not in (1, 3, 4)):
        raise ValueError("Expected HxW grayscale or HxWxC image")
    if not 0 < cutoff <= 0.5 or order < 1:
        raise ValueError("Require 0 < cutoff <= 0.5 cycles/pixel and order >= 1")
    height, width = source.shape[:2]
    fy, fx = np.meshgrid(fftfreq(height), fftfreq(width), indexing="ij")
    radius = np.hypot(fy, fx)
    response = 1.0 / (1.0 + (radius / cutoff) ** (2 * order))
    if source.ndim == 2:
        return np.clip(ifft2(fft2(source) * response).real, 0.0, 1.0)
    return np.stack([np.clip(ifft2(fft2(source[..., c]) * response).real, 0.0, 1.0)
                     for c in range(source.shape[2])], axis=-1)


def psnr(reference: np.ndarray, estimate: np.ndarray) -> float:
    mse = float(np.mean((np.asarray(reference, dtype=np.float64) - estimate) ** 2))
    return float("inf") if mse == 0 else 10.0 * np.log10(1.0 / mse)


def structural_similarity(reference: np.ndarray, estimate: np.ndarray) -> float:
    """Gaussian-window SSIM, calculated per channel then averaged (data range 1)."""
    from scipy.ndimage import gaussian_filter

    x, y = np.asarray(reference, dtype=np.float64), np.asarray(estimate, dtype=np.float64)
    if x.shape != y.shape:
        raise ValueError("Images must have identical shapes")
    if x.ndim == 2:
        x, y = x[..., None], y[..., None]
    values = []
    c1, c2 = 0.01**2, 0.03**2
    for channel in range(x.shape[-1]):
        a, b = x[..., channel], y[..., channel]
        mean_a, mean_b = gaussian_filter(a, 1.5), gaussian_filter(b, 1.5)
        var_a = gaussian_filter(a * a, 1.5) - mean_a * mean_a
        var_b = gaussian_filter(b * b, 1.5) - mean_b * mean_b
        covariance = gaussian_filter(a * b, 1.5) - mean_a * mean_b
        score = (((2 * mean_a * mean_b + c1) * (2 * covariance + c2)) /
                 ((mean_a**2 + mean_b**2 + c1) * (var_a + var_b + c2)))
        values.append(float(np.mean(score)))
    return float(np.mean(values))


def load_rgb(path: Path, size: int = 224) -> np.ndarray:
    with Image.open(path) as image:
        image = image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
        return np.asarray(image, dtype=np.float32) / 255.0


if nn is not None:
    class LegacyHognoseCNN(nn.Module):
        """Three-convolution 2024 CNN, converted to raw multilabel logits."""

        def __init__(self, outputs: int):
            super().__init__()
            if outputs < 1:
                raise ValueError("outputs must be >= 1")
            self.features = nn.Sequential(
                nn.Conv2d(3, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2))
            self.head = nn.Sequential(nn.Flatten(), nn.Linear(64 * 28 * 28, 128), nn.ReLU(),
                                      nn.Dropout(0.5), nn.Linear(128, outputs))

        def forward(self, x):
            return self.head(self.features(x))
else:
    class LegacyHognoseCNN:  # pragma: no cover - only reached without PyTorch
        def __init__(self, outputs: int):
            raise ImportError("LegacyHognoseCNN requires PyTorch")


def experiment(image_dir: Path, *, seed: int = 2024, noise_std: float = 20 / 255,
               mu: float = 0.08, step: float = 0.24, iterations: int = 80) -> dict:
    """Run deterministic synthetic Gaussian noise experiment on local images."""
    paths = sorted(image_dir.glob("figure*.png"))
    if not paths:
        paths = sorted(p for p in image_dir.iterdir()
                       if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not paths:
        raise ValueError(f"No local images found in {image_dir}")
    rng = np.random.default_rng(seed)
    per_image = []
    for path in paths:
        clean = load_rgb(path)
        noisy = np.clip(clean + rng.normal(0.0, noise_std, clean.shape), 0.0, 1.0)
        denoised = np.clip(fppa_tv_denoise(noisy, mu=mu, step=step,
                                           iterations=iterations), 0.0, 1.0)
        per_image.append({"name": path.name,
                          "noisy_psnr_db": psnr(clean, noisy),
                          "fppa_psnr_db": psnr(clean, denoised),
                          "noisy_ssim": structural_similarity(clean, noisy),
                          "fppa_ssim": structural_similarity(clean, denoised)})
    return {"experiment": "deterministic synthetic Gaussian noise; no model training",
            "image_count": len(paths), "input_images": [p.name for p in paths],
            "seed": seed, "resize": "RGB bilinear 224x224", "noise_std_0_1": noise_std,
            "fppa": {"mu": mu, "step": step, "iterations": iterations,
                     "operator": "anisotropic ROF TV, RGB channels independently"},
            "metrics": {key: round(float(np.mean([row[key] for row in per_image])), 4)
                        for key in ("noisy_psnr_db", "fppa_psnr_db",
                                    "noisy_ssim", "fppa_ssim")},
            "per_image": per_image,
            "classification_claim": "none; preprocessing effect on morph classification is unproven"}


def benchmark(device: str = "cpu", warmup: int = 10, repeats: int = 50) -> dict:
    """Measure initialized, random-weight inference; no downloads or label claims."""
    import torch
    from torch import nn
    from torchvision.models import mobilenet_v3_small

    torch.set_num_threads(1)
    target = torch.device(device)
    models = {"legacy_cnn_3conv": LegacyHognoseCNN(outputs=18).to(target).eval(),
              "mobilenet_v3_small": mobilenet_v3_small(weights=None).to(target).eval()}
    sample = torch.zeros(1, 3, 224, 224, device=target)
    measurements = {}
    for name, model in models.items():
        with torch.inference_mode():
            for _ in range(warmup):
                model(sample)
            if target.type == "mps":
                torch.mps.synchronize()
            timings = []
            for _ in range(repeats):
                start = time.perf_counter()
                model(sample)
                if target.type == "mps":
                    torch.mps.synchronize()
                timings.append((time.perf_counter() - start) * 1000)
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        measurements[name] = {
            "parameters": sum(p.numel() for p in model.parameters()),
            "state_dict_bytes": buffer.tell(),
            "latency_ms_median": round(statistics.median(timings), 3),
            "latency_ms_p95": round(float(np.percentile(timings, 95)), 3),
        }
    return {"benchmark": "single-image forward, batch=1, 224x224 RGB, random initialization",
            "device": str(target), "torch_version": torch.__version__,
            "warmup_runs": warmup, "timed_runs": repeats,
            "models": measurements,
            "note": "Not accuracy or training evidence; measured size is uncompressed state_dict serialization."}


def masked_bce_with_logits(logits, targets, known_mask):
    """Mean BCE over known labels only; unknown labels contribute no loss."""
    import torch.nn.functional as functional

    losses = functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    mask = known_mask.to(dtype=losses.dtype)
    return (losses * mask).sum() / mask.sum().clamp(min=1.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    exp = sub.add_parser("experiment", help="measure FPPA on local photos with synthetic noise")
    exp.add_argument("image_dir", type=Path)
    exp.add_argument("--output", type=Path)
    exp.add_argument("--seed", type=int, default=2024)
    exp.add_argument("--noise-std", type=float, default=20 / 255)
    exp.add_argument("--mu", type=float, default=0.08)
    exp.add_argument("--step", type=float, default=0.24)
    exp.add_argument("--iterations", type=int, default=80)
    bench = sub.add_parser("benchmark", help="measure local CNN inference latency and serialized size")
    bench.add_argument("--device", default="cpu")
    bench.add_argument("--warmup", type=int, default=10)
    bench.add_argument("--repeats", type=int, default=50)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "experiment":
        result = experiment(args.image_dir, seed=args.seed, noise_std=args.noise_std,
                            mu=args.mu, step=args.step, iterations=args.iterations)
        rendered = json.dumps(result, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n")
        print(rendered)
    else:
        if args.warmup < 0 or args.repeats < 1:
            raise SystemExit("warmup must be >= 0 and repeats must be >= 1")
        print(json.dumps(benchmark(args.device, args.warmup, args.repeats), indent=2))


if __name__ == "__main__":
    main()

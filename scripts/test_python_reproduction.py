#!/usr/bin/env python3
"""Deterministic unit tests for the Python image-pipeline reproduction."""

import unittest

import numpy as np

from python_reproduction import (LegacyHognoseCNN, adjoint_difference,
                                butterworth_lowpass, forward_difference,
                                fppa_tv_denoise, masked_bce_with_logits,
                                psnr, structural_similarity)


class FppaTests(unittest.TestCase):
    def test_difference_operators_are_adjoint(self):
        rng = np.random.default_rng(8)
        image = rng.normal(size=(7, 9, 3))
        p, q = rng.normal(size=image.shape), rng.normal(size=image.shape)
        dx, dy = forward_difference(image)
        lhs = np.sum(dx * p) + np.sum(dy * q)
        rhs = np.sum(image * adjoint_difference(p, q))
        self.assertAlmostEqual(float(lhs), float(rhs), places=10)

    def test_constant_rgb_is_preserved(self):
        image = np.full((16, 13, 3), (0.2, 0.5, 0.8), dtype=float)
        result = fppa_tv_denoise(image, iterations=5)
        self.assertEqual(result.shape, image.shape)
        np.testing.assert_allclose(result, image, atol=1e-12)

    def test_fppa_reduces_seeded_noise_and_keeps_channels(self):
        y, x = np.mgrid[:40, :48]
        clean = np.stack((x / 47, y / 39, (x + y) / 86), axis=-1)
        rng = np.random.default_rng(42)
        noisy = np.clip(clean + rng.normal(0, 0.05, clean.shape), 0, 1)
        denoised = np.clip(fppa_tv_denoise(noisy, mu=0.06, iterations=50), 0, 1)
        self.assertEqual(denoised.shape, noisy.shape)
        self.assertGreater(psnr(clean, denoised), psnr(clean, noisy))
        self.assertGreater(structural_similarity(clean, denoised),
                           structural_similarity(clean, noisy))

    def test_filter_is_optional_and_preserves_rgb_shape(self):
        rng = np.random.default_rng(3)
        image = rng.random((19, 21, 3))
        result = butterworth_lowpass(image)
        self.assertEqual(result.shape, image.shape)
        self.assertTrue(np.isfinite(result).all())
        self.assertTrue(np.all((result >= 0) & (result <= 1)))

    def test_invalid_fppa_parameters_fail_closed(self):
        with self.assertRaises(ValueError):
            fppa_tv_denoise(np.zeros((2, 2)), step=0.25)


class ModelTests(unittest.TestCase):
    def test_legacy_model_emits_logits_with_requested_outputs(self):
        import torch
        model = LegacyHognoseCNN(outputs=7).eval()
        with torch.inference_mode():
            logits = model(torch.zeros(1, 3, 224, 224))
        self.assertEqual(tuple(logits.shape), (1, 7))
        self.assertFalse(torch.all((logits >= 0) & (logits <= 1)))

    def test_masked_bce_ignores_unknown_cells(self):
        import torch
        logits = torch.tensor([[0.0, 10.0]])
        targets = torch.tensor([[1.0, 0.0]])
        loss = masked_bce_with_logits(logits, targets, torch.tensor([[1.0, 0.0]]))
        self.assertAlmostEqual(float(loss), float(torch.nn.functional.softplus(torch.tensor(0.0))), places=6)


if __name__ == "__main__":
    unittest.main()

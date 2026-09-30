#!/usr/bin/env python3
"""Tests for the private review-export to gated manifest bridge."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from build_reviewed_manifest import build_manifest


class BuildReviewedManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "incoming-review"
        (self.root / "previews").mkdir(parents=True)
        self.source = Path(self.temp.name) / "source.jpg"
        self.source.write_bytes(b"original source bytes")
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.preview = self.root / "previews" / "002-abcdef123456.jpg"
        Image.new("RGB", (24, 20), (180, 120, 80)).save(self.preview)
        self.inventory_path = self.root / "reviewed_inventory.json"
        self.inventory_path.write_text("{}", encoding="utf-8")
        self.inventory = {"records": [{
            "index": 2, "sha256": self.digest, "source_path": str(self.source),
            "preview": "previews/002-abcdef123456.jpg",
            "visual_triage": "candidate_western_hognose",
        }]}
        self.review = {
            "source_index": 2, "source_sha256": self.digest,
            "visual_triage": "candidate_western_hognose",
            "species_review": "western_hognose", "source_scope": "captive_morph",
            "source_url": "https://example.org/animal/2", "individual_id": "snake-2",
            "morph_labels": [{"trait_id": "albino", "state": "expressed"}],
            "evidence_type": "expert_phenotype_review",
            "evidence_url": "https://example.org/review/2", "claim_scope": "phenotype",
            "image_rights": "owner_permission",
            "rights_evidence_url": "https://example.org/permission/2",
            "rights_reviewed_by": "Rights reviewer",
            "rights_scopes": {"training": True, "evaluation": True,
                              "hackathon_demo": False, "public_web": False},
            "attribution": "Photographer 2", "review_status": "reviewed",
            "reviewer": "Morph reviewer",
        }

    def tearDown(self):
        self.temp.cleanup()

    def build(self, review=None, inventory=None):
        return build_manifest({"schema_version": "incoming-review-v1",
                               "records": [review or self.review]},
                              inventory or self.inventory, self.inventory_path)

    def test_valid_review_maps_labels_and_uses_private_preview(self):
        result = self.build()
        self.assertEqual(result["eligible_candidates"], 1)
        self.assertEqual(result["eligible_individuals"], 1)
        row = result["records"][0]
        self.assertEqual(row["labels"], {"albino:expressed": 1})
        self.assertEqual(row["image"], str(self.preview.resolve()))
        self.assertEqual(row["claim_scope"], "phenotype")

    def test_not_recorded_state_is_omitted_as_unknown(self):
        review = {**self.review, "morph_labels": [
            {"trait_id": "albino", "state": "not_recorded"},
            {"trait_id": "sable", "state": "expressed"},
        ]}
        result = self.build(review)
        self.assertEqual(result["eligible_candidates"], 1)
        self.assertEqual(result["records"][0]["labels"], {"sable:expressed": 1})

    def test_not_recorded_does_not_bypass_unknown_trait_validation(self):
        review = {**self.review, "morph_labels": [
            {"trait_id": "not-a-real-trait", "state": "not_recorded"},
            {"trait_id": "sable", "state": "expressed"},
        ]}
        result = self.build(review)
        self.assertEqual(result["eligible_candidates"], 0)
        self.assertIn("unknown trait/state entry: not-a-real-trait:not_recorded",
                      result["rejected"][0]["reasons"])

    def test_unknown_species_and_wrong_scope_are_not_promoted(self):
        review = {**self.review, "species_review": "uncertain", "source_scope": "captive_pet"}
        result = self.build(review)
        self.assertEqual(result["eligible_candidates"], 0)
        reasons = set(result["rejected"][0]["reasons"])
        self.assertIn("manual species review must confirm Western Hognose", reasons)
        self.assertIn("source_scope must be captive_morph", reasons)

    def test_changed_original_bytes_are_rejected(self):
        self.source.write_bytes(b"changed bytes")
        result = self.build()
        self.assertEqual(result["eligible_candidates"], 0)
        self.assertIn("original source image SHA-256 no longer matches inventory",
                      result["rejected"][0]["reasons"])

    def test_preview_path_traversal_is_rejected(self):
        inventory = {"records": [{**self.inventory["records"][0],
                                  "preview": "previews/../../source.jpg"}]}
        result = self.build(inventory=inventory)
        self.assertEqual(result["eligible_candidates"], 0)
        self.assertTrue(any("preview path escapes" in reason
                            for reason in result["rejected"][0]["reasons"]))

    def test_missing_rights_and_label_evidence_fail_existing_gate(self):
        review = {**self.review, "rights_scopes": {"training": True},
                  "morph_labels": []}
        result = self.build(review)
        self.assertEqual(result["eligible_candidates"], 0)
        reasons = " ".join(result["rejected"][0]["reasons"])
        self.assertIn("rights_scopes must explicitly record", reasons)
        self.assertIn("at least one reviewed positive morph label is required", reasons)

    def test_duplicate_export_row_is_reported(self):
        result = build_manifest({"schema_version": "incoming-review-v1",
                                 "records": [self.review, self.review]},
                                self.inventory, self.inventory_path)
        self.assertEqual(result["eligible_candidates"], 1)
        self.assertEqual(result["rejected_records"], 1)
        self.assertIn("duplicate review export entry", result["rejected"][0]["reasons"])


if __name__ == "__main__":
    unittest.main()

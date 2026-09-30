"""Run: python -m unittest discover -s tests/demo -v."""
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from fastapi import HTTPException
from PIL import Image

from demo.service import Catalog, Config, ModelResult, create_app, ROOT


def result(traits=None, refs=None, species="western_hognose", count=1, usable=True):
    return ModelResult.model_validate({"assessment": {"species": species, "animal_count": count, "usable": usable,
        "observations": ["Visible snake"], "reason": "Visible morphology"}, "candidates": [] if traits is None else [
        {"traits": traits, "support_level": "moderate", "visible_evidence": ["Pale pigment"], "uncertainties": ["Lighting"],
         "reference_ids": refs or []}], "limitations": ["Reference examples only"]})


class FakeProvider:
    def __init__(self, outputs, error=None):
        self.outputs, self.error, self.calls = outputs, error, []
    def configured(self):
        pass
    async def ready(self):
        if self.error:
            raise HTTPException(503, {"code": "model_missing", "message": "Missing model"})
    async def infer(self, prompt, images):
        self.calls.append((prompt, len(images)))
        return self.outputs.pop(0)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "data/ontology.json").write_text((ROOT / "data/ontology.json").read_text())
        im = Image.new("RGB", (40, 40), "white")
        im.save(self.root / "data/reference.jpg")
        self.png = io.BytesIO()
        im.save(self.png, "PNG")
        self.refs = [{"id": "albino-ref", "image": "data/reference.jpg", "traits": [{"trait_id": "albino", "state": "expressed"}]}]
        (self.root / "data/demo_references.json").write_text(json.dumps({"schema_version": "1.0.0", "images": self.refs}))
        (self.root / "index.html").write_text("demo")
        (self.root / ".env").write_text("SECRET=hidden")
        self.config = Config("ollama", "qwen3-vl:4b-instruct", "http://127.0.0.1:11434", "", 1)
    def tearDown(self):
        self.temp.cleanup()
    def client(self, provider):
        return TestClient(create_app(self.root, self.config, provider))
    def post(self, client, lang="en", raw=None):
        return client.post("/api/analyze", files={"image": ("x.png", raw if raw is not None else self.png.getvalue(), "image/png")}, data={"lang": lang})
    def test_two_stages_alias_and_reference(self):
        traits = [{"trait_id": "albino", "state": "expressed"}, {"trait_id": "sable", "state": "expressed"}]
        provider = FakeProvider([result(traits), result(traits, ["albino-ref"])])
        response = self.post(self.client(provider), "zh")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["candidates"][0]["name_en"], "Sunburst")
        self.assertEqual(data["candidates"][0]["references"], self.refs)
        self.assertEqual([c[1] for c in provider.calls], [1, 2])
        self.assertIn("Chinese", provider.calls[0][0])
    def test_non_target_and_multiple_stop_before_compare(self):
        for species, count in [("non_target", 0), ("uncertain", 1), ("western_hognose", 2)]:
            provider = FakeProvider([result(species=species, count=count)])
            data = self.post(self.client(provider)).json()
            self.assertEqual(data["candidates"], [])
            self.assertEqual(len(provider.calls), 1)
    def test_invalid_trait_conflict_reference_rejected(self):
        for traits, refs in [([{ "trait_id": "white_wall", "state": "expressed"}], []),
                             ([{"trait_id": "albino", "state": "heterozygous"}], []),
                             ([{"trait_id": "anaconda", "state": "homozygous"}, {"trait_id": "anaconda", "state": "heterozygous"}], []),
                             ([{"trait_id": "albino", "state": "expressed"}], ["invented"])]:
            response = self.post(self.client(FakeProvider([result(traits, refs)])))
            self.assertEqual(response.status_code, 502)
    def test_bad_image_model_missing_and_static_security(self):
        client = self.client(FakeProvider([], error=True))
        self.assertEqual(self.post(client, raw=b"garbage").status_code, 400)
        self.assertEqual(self.post(client).status_code, 503)
        self.assertFalse(client.get("/api/status").json()["ready"])
        for path in ["/.env", "/.git/config", "/requirements-demo.txt", "/data/../.env"]:
            self.assertEqual(client.get(path).status_code, 404)
        self.assertEqual(client.get("/data/reference.jpg").status_code, 200)
    def test_failed_output_trace_and_document_assets(self):
        import os
        from unittest.mock import patch
        class InvalidProvider(FakeProvider):
            async def infer(self, prompt, images):
                self.last_raw_content = '{"malformed": true}'
                raise HTTPException(502, {"code": "invalid_model_output", "message": "Invalid"})
        trace = self.root / "private-traces"
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text("guide")
        client = self.client(InvalidProvider([]))
        with patch.dict(os.environ, {"HOGMORPH_TRACE_DIR": str(trace)}):
            self.assertEqual(self.post(client).status_code, 502)
        records = list(trace.glob("*.json"))
        self.assertEqual(len(records), 1)
        captured = json.loads(records[0].read_text())
        self.assertEqual(captured["raw_response"], '{"malformed": true}')
        self.assertEqual(captured["error_code"], "invalid_model_output")
        self.assertEqual(client.get("/docs/guide.md").status_code, 200)
        self.assertEqual(client.get("/private-traces/" + records[0].name).status_code, 404)
    def test_large_upload_remains_memory_and_is_closed(self):
        from unittest.mock import patch
        import tempfile as temp_module
        import starlette.formparsers as parsers
        files = []
        original = temp_module.SpooledTemporaryFile
        def spool(*args, **kwargs):
            resource = original(*args, **kwargs)
            files.append(resource)
            return resource
        raw = io.BytesIO()
        Image.new("RGB", (900, 900), "green").save(raw, "BMP")
        self.assertGreater(len(raw.getvalue()), 1024 * 1024)
        provider = FakeProvider([result(species="non_target", count=0)])
        with patch.object(parsers, "SpooledTemporaryFile", spool):
            response = self.post(self.client(provider), raw=raw.getvalue())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(files)
        self.assertTrue(all(not f._rolled and f.closed for f in files))

    def test_total_limit_with_length_and_chunked_body(self):
        from unittest.mock import patch
        provider = FakeProvider([])
        client = self.client(provider)
        with patch("demo.service.MAX_MULTIPART_BYTES", 1024):
            self.assertEqual(self.post(client, raw=b"x" * 2048).status_code, 413)
            body = b'--abc\r\nContent-Disposition: form-data; name="image"; filename="x.png"\r\n\r\n' + b"x" * 2048 + b"\r\n--abc--\r\n"
            response = client.post("/api/analyze", content=iter([body[:900], body[900:]]),
                                   headers={"content-type": "multipart/form-data; boundary=abc", "transfer-encoding": "chunked"})
            self.assertEqual(response.status_code, 413)
        self.assertEqual(provider.calls, [])

    def test_diverse_positive_only_reference_selection(self):
        catalog = Catalog(self.root)
        anaconda = {"trait_id": "anaconda", "state": "heterozygous"}
        arctic = {"trait_id": "arctic", "state": "heterozygous"}
        candidates = result([anaconda, arctic]).candidates
        refs = [dict(id="a1", traits=[anaconda]), dict(id="a2", traits=[anaconda]),
                dict(id="a3", traits=[anaconda]), dict(id="b1", traits=[arctic])]
        selected = catalog.select(candidates, refs)
        self.assertEqual([r["id"] for r in selected], ["a1", "b1"])
        # An extra known label on a reference never subtracts relevance for an unknown upload label.
        refs = [dict(id="a", traits=[anaconda, {"trait_id": "albino", "state": "expressed"}]), dict(id="b", traits=[anaconda])]
        self.assertEqual(catalog.select(result([anaconda]).candidates, refs)[0]["id"], "a")
        provider = FakeProvider([result([{"trait_id": "albino", "state": "expressed"}]), result([{"trait_id": "albino", "state": "expressed"}], ["albino-ref"])])
        self.assertEqual(self.post(self.client(provider)).status_code, 200)
        self.assertIn('"labels_complete": false', provider.calls[1][0])
        self.assertIn("image 1 ONLY", provider.calls[1][0])
    def test_visual_codebook_is_general_and_preserves_rejection(self):
        from demo.service import prompt_for, VISUAL_CODEBOOK_SOURCES
        prompt = prompt_for(Catalog(self.root), "en")
        self.assertIn("Species is assessed from anatomy", prompt)
        self.assertIn("Red/ruby eyes are compatible", prompt)
        self.assertIn("almost patternless dorsum", prompt)
        self.assertIn("absence of black does NOT exclude Sable", prompt)
        self.assertIn("one to three weak hypotheses", prompt)
        self.assertIn("Clear non-target animals remain non_target", prompt)
        self.assertIn("If species is not confidently Western Hognose", prompt)
        self.assertEqual(len(VISUAL_CODEBOOK_SOURCES), 7)
        self.assertNotIn("figure06", prompt)
        self.assertNotIn("x.png", prompt)
    def test_alternate_state_reference_and_provisional_contract(self):
        from demo.service import prompt_for
        catalog = Catalog(self.root)
        traits = [{"trait_id": "arctic", "state": "heterozygous"}]
        hypothesis = result(traits).candidates
        ref = {"id": "super-arctic", "traits": [{"trait_id": "arctic", "state": "homozygous"}]}
        self.assertEqual(catalog.select(hypothesis, [ref]), [ref])
        unrelated = {"id": "albino", "traits": [{"trait_id": "albino", "state": "expressed"}]}
        self.assertEqual(len(catalog.select(hypothesis, [unrelated])), 1)
        prompt = prompt_for(catalog, "en", [ref], [hypothesis[0].model_dump()])
        self.assertIn("Provisional first-pass hypotheses (NOT ground truth)", prompt)
        self.assertIn("Every proposed component requires its own visible cue", prompt)
        self.assertIn("prefer the minimal supported component set", prompt)
        self.assertIn("Do not infer unseen belly features", prompt)
        self.assertIn("Lack of pedigree/genetic proof alone", prompt)
        self.assertIn("ACTUAL visible head/snout, eyes, dorsal pattern and pigment", prompt)
        self.assertIn("explicitly say when a feature is not visible", prompt)
        self.assertIn("never force a candidate", prompt)
    def test_duplicate_hypotheses_and_references_normalized_after_validation(self):
        from demo.service import validate_result
        catalog = Catalog(self.root)
        traits = [{"trait_id": "albino", "state": "expressed"}]
        value = result(traits, ["albino-ref", "albino-ref"])
        duplicate = value.candidates[0].model_copy(deep=True)
        duplicate.visible_evidence = ["Different evidence must not be merged"]
        value.candidates.append(duplicate)
        validate_result(value, catalog, {"albino-ref"})
        self.assertEqual(len(value.candidates), 1)
        self.assertEqual(value.candidates[0].reference_ids, ["albino-ref"])
        self.assertEqual(value.candidates[0].visible_evidence, ["Pale pigment"])
        invalid = result(traits)
        duplicate = invalid.candidates[0].model_copy(deep=True)
        duplicate.reference_ids = ["invented"]
        invalid.candidates.append(duplicate)
        with self.assertRaises(HTTPException):
            validate_result(invalid, catalog, {"albino-ref"})
    def test_same_signature_retrieval_uses_visual_match_and_caches_features(self):
        catalog = Catalog(self.root)
        Image.new("RGB", (512, 512), "white").save(self.root / "data/course.jpg")
        Image.new("RGB", (512, 512), "red").save(self.root / "data/genes.jpg")
        traits = [{"trait_id": "albino", "state": "expressed"}]
        refs = [dict(id="first-course", image="data/course.jpg", traits=traits, source_group="course"),
                dict(id="later-genes", image="data/genes.jpg", traits=traits, source_group="genes")]
        uploaded = (self.root / "data/genes.jpg").read_bytes()
        selected = catalog.select(result(traits).candidates, refs, uploaded)
        self.assertEqual([r["id"] for r in selected], ["later-genes"])
        self.assertEqual(len(catalog._feature_cache), 2)
        self.assertEqual(catalog.select(result(traits).candidates, list(reversed(refs)), uploaded), selected)
        self.assertEqual(len(catalog._feature_cache), 2)
        self.assertNotIn("similarity", selected[0])
        (self.root / "data/genes.jpg").unlink()
        with self.assertRaises(HTTPException):
            catalog.select(result(traits).candidates, refs, uploaded)

    def test_low_resolution_representative_does_not_win_only_by_visual_similarity(self):
        catalog = Catalog(self.root)
        Image.new("RGB", (512, 512), "white").save(self.root / "data/high.jpg")
        Image.new("RGB", (8, 8), "red").save(self.root / "data/tiny.jpg")
        traits = [{"trait_id": "albino", "state": "expressed"}]
        refs = [dict(id="tiny", image="data/tiny.jpg", traits=traits), dict(id="usable", image="data/high.jpg", traits=traits)]
        selected = catalog.select(result(traits).candidates, refs, (self.root / "data/tiny.jpg").read_bytes())
        self.assertEqual(selected[0]["id"], "usable")
    def test_usable_target_without_first_hypothesis_compares_real_references(self):
        traits = [{"trait_id": "albino", "state": "expressed"}]
        provider = FakeProvider([result(), result(traits, ["albino-ref"])])
        response = self.post(self.client(provider))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "candidates")
        self.assertEqual([call[1] for call in provider.calls], [1, 2])
        provider = FakeProvider([result(), result()])
        response = self.post(self.client(provider))
        self.assertEqual(response.json()["status"], "insufficient_evidence")
        self.assertEqual(len(provider.calls), 2)
        provider = FakeProvider([result(usable=False)])
        response = self.post(self.client(provider))
        self.assertEqual(response.json()["status"], "insufficient_evidence")
        self.assertEqual(len(provider.calls), 1)
        catalog = Catalog(self.root)
        refs = [dict(id="a", traits=traits), dict(id="b", traits=[{"trait_id": "arctic", "state": "heterozygous"}]),
                dict(id="c", traits=[{"trait_id": "arctic", "state": "homozygous"}]), dict(id="duplicate", traits=traits)]
        selected = catalog.select([], refs, self.png.getvalue())
        self.assertEqual(len(selected), 3)
        signatures = {tuple((t["trait_id"], t["state"]) for t in r["traits"]) for r in selected}
        self.assertEqual(len(signatures), 3)
    def test_local_guide_assets_exact_manifest_allowlist(self):
        folder = self.root / "data/reference_images"
        folder.mkdir()
        Image.new("RGB", (20, 20), "white").save(folder / "listed.jpeg")
        Image.new("RGB", (20, 20), "white").save(folder / "unlisted.jpg")
        (self.root / "source").mkdir()
        (self.root / "source/private.docx").write_bytes(b"private course document")
        manifest = {"images": [{"file": "reference_images/listed.jpeg"}, {"file": "reference_images/missing.png"},
                               {"file": "reference_images/../../source/private.docx"}, {"file": "../.env"}, None, {"file": 123}]}
        (self.root / "data/reference_gallery.json").write_text(json.dumps(manifest))
        client = self.client(FakeProvider([]))
        self.assertEqual(client.get("/data/reference_images/listed.jpeg").status_code, 200)
        for path in ["/data/reference_images/unlisted.jpg", "/data/reference_images/missing.png", "/source/private.docx",
                     "/data/reference_images/../../source/private.docx", "/.env"]:
            self.assertEqual(client.get(path).status_code, 404)
        self.assertEqual(client.get("/api/references").json()["images"], self.refs)
        for invalid in ["not-json", "null", '{"images":null}', '{"images":{}}']:
            (self.root / "data/reference_gallery.json").write_text(invalid)
            self.assertEqual(client.get("/data/reference_images/listed.jpeg").status_code, 404)

    def test_local_guide_symlink_targets_are_never_served(self):
        folder = self.root / "data/reference_images"
        folder.mkdir()
        (self.root / "private.docx").write_bytes(b"private document")
        outside = Path(self.temp.name).parent / (self.root.name + "-outside.jpg")
        outside.write_bytes(b"outside secret")
        try:
            for name, target in [("private.jpg", self.root / "private.docx"), ("secret.jpg", self.root / ".env"), ("outside.jpg", outside)]:
                (folder / name).symlink_to(target)
            (self.root / "data/reference_gallery.json").write_text(json.dumps({"images": [
                {"file": "reference_images/" + name} for name in ["private.jpg", "secret.jpg", "outside.jpg"]]}))
            client = self.client(FakeProvider([]))
            for name in ["private.jpg", "secret.jpg", "outside.jpg"]:
                self.assertEqual(client.get("/data/reference_images/" + name).status_code, 404)
            for path in folder.iterdir():
                path.unlink()
            folder.rmdir()
            actual = self.root / "private-folder"
            actual.mkdir()
            Image.new("RGB", (20, 20), "white").save(actual / "ordinary.jpg")
            folder.symlink_to(actual, target_is_directory=True)
            (self.root / "data/reference_gallery.json").write_text(json.dumps({"images": [{"file": "reference_images/ordinary.jpg"}]}))
            self.assertEqual(client.get("/data/reference_images/ordinary.jpg").status_code, 404)
        finally:
            outside.unlink(missing_ok=True)

    def test_names(self):
        catalog = Catalog(self.root)
        self.assertEqual(catalog.names([{"trait_id": "anaconda", "state": "homozygous"}])[0], "Superconda")
        compound = catalog.names([{"trait_id": "anaconda", "state": "homozygous"}, {"trait_id": "albino", "state": "expressed"}])
        self.assertEqual(compound, ("Albino + Superconda", "白化 + 超级康达"))
        self.assertEqual(catalog.names([{"trait_id": "albino", "state": "expressed"}, {"trait_id": "axanthic", "state": "expressed"}])[0], "Snow")

if __name__ == "__main__":
    unittest.main()

class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_format_and_invalid_response(self):
        from demo.service import Provider
        class MockProvider(Provider):
            async def request(self, method, endpoint, **kwargs):
                self.sent = (method, endpoint, kwargs)
                return self.answer
        provider = MockProvider(Config("openai", "vision-model", "https://example.org/v1", "key", 1))
        provider.answer = {"choices": [{"message": {"content": result().model_dump_json()}}]}
        parsed = await provider.infer("Inspect image", [b"test-image"])
        self.assertEqual(parsed.assessment.species, "western_hognose")
        method, route, kwargs = provider.sent
        self.assertEqual(route, "/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer key")
        self.assertTrue(kwargs["json"]["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        provider.answer = {"choices": [{"message": {"content": "not JSON"}}]}
        with self.assertRaises(HTTPException) as error:
            await provider.infer("Inspect", [b"test"])
        self.assertEqual(error.exception.detail["code"], "invalid_model_output")
    async def test_ollama_disables_thinking_and_checks_vision(self):
        from demo.service import Provider
        class NativeProvider(Provider):
            async def request(self, method, endpoint, **kwargs):
                if endpoint == "/api/tags":
                    return {"models": [{"name": "qwen3-vl:4b-instruct"}]}
                if endpoint == "/api/show":
                    return {"capabilities": self.capabilities}
                self.sent = kwargs["json"]
                return {"message": {"content": result().model_dump_json(), "thinking": "private"}, "done_reason": "stop", "eval_count": 99}
        provider = NativeProvider(Config("ollama", "qwen3-vl:4b-instruct", "http://127.0.0.1:11434", "", 1))
        provider.capabilities = ["completion"]
        with self.assertRaises(HTTPException) as error:
            await provider.ready()
        self.assertEqual(error.exception.detail["code"], "model_not_vision")
        provider.capabilities = ["completion", "vision", "thinking"]
        await provider.ready()
        await provider.infer("Inspect", [b"image"])
        self.assertFalse(provider.sent["think"])
        self.assertEqual(provider.sent["options"]["num_ctx"], 16384)
        self.assertEqual(provider.last_response_metadata, {"done_reason": "stop", "eval_count": 99, "thinking_char_count": 7})
        self.assertNotIn("private", provider.last_raw_content)
    async def test_missing_model_and_timeout(self):
        from demo.service import Provider
        import httpx
        from unittest.mock import patch
        class EmptyProvider(Provider):
            async def request(self, *args, **kwargs):
                return {"models": []}
        with self.assertRaises(HTTPException) as error:
            await EmptyProvider(Config("ollama", "missing", "http://127.0.0.1:11434", "", 1)).ready()
        self.assertEqual(error.exception.detail["code"], "model_missing")
        with patch.object(httpx.AsyncClient, "request", side_effect=httpx.ReadTimeout("timeout")):
            with self.assertRaises(HTTPException) as error:
                await Provider(Config("ollama", "m", "http://127.0.0.1:11434", "", 1)).ready()
        self.assertEqual(error.exception.detail["code"], "model_timeout")
    async def test_secret_urls_and_remote_ollama_rejected(self):
        from demo.service import Provider
        for url in ["https://key:secret@example.org", "https://example.org?token=secret", "http://example.org"]:
            with self.assertRaises(HTTPException):
                Provider(Config("ollama", "m", url, "", 1)).configured()

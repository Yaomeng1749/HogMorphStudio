"""Deterministic API tests for server-side photo exclusion and restoration."""

import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("incoming_review_server", ROOT_DIR / "scripts" / "serve_incoming_review.py")
server_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server_module)


class ExclusionAPITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = (Path(self.temp.name) / "incoming-review").resolve()
        self.root = base
        self.previews = base / "previews"
        self.previews.mkdir(parents=True)
        self.index = 7
        self.duplicate_index = 8
        self.digest = "a" * 64
        self.preview_name = f"{self.index:03d}-{self.digest[:12]}.jpg"
        self.duplicate_preview = f"{self.duplicate_index:03d}-{self.digest[:12]}.jpg"
        (self.previews / self.preview_name).write_bytes(b"jpeg-test-bytes")
        (self.previews / self.duplicate_preview).write_bytes(b"jpeg-test-bytes")
        (base / "active_inventory.json").write_text(json.dumps({"records": [{
            "index": self.index, "sha256": self.digest, "preview": f"previews/{self.preview_name}",
            "visual_triage": "candidate_western_hognose", "source_path": "/private/original.jpg",
        }, {
            "index": self.duplicate_index, "sha256": self.digest, "preview": f"previews/{self.duplicate_preview}",
            "visual_triage": "uncertain", "source_path": "/private/duplicate-original.jpg",
        }]}), encoding="utf-8")
        server_module.ROOT = base
        server_module.PREVIEWS = self.previews
        server_module.REVIEW_STATE = base / "review_state.json"
        self.httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def get_json(self, path):
        with urlopen(self.base_url + path, timeout=3) as response:
            return json.load(response)

    def mutate(self, action, index=None, digest=None):
        body = json.dumps({"index": self.index if index is None else index,
                           "sha256": self.digest if digest is None else digest}).encode()
        request = Request(self.base_url + "/api/" + action, data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=3) as response:
            return response.status, json.load(response)

    def test_exclude_blocks_active_inventory_and_preview_then_restore(self):
        self.assertEqual(len(self.get_json("/api/inventory")), 2)
        self.mutate("exclude")
        state = json.loads(server_module.REVIEW_STATE.read_text(encoding="utf-8"))
        self.assertEqual(state["excluded"], [{"index": self.index, "sha256": self.digest},
                                              {"index": self.duplicate_index, "sha256": self.digest}])
        self.assertEqual(self.get_json("/api/inventory"), [])
        self.assertEqual(self.get_json("/api/excluded"), [
            {"index": self.index, "sha256": self.digest, "visual_triage": "candidate_western_hognose"},
            {"index": self.duplicate_index, "sha256": self.digest, "visual_triage": "uncertain"},
        ])
        for name in (self.preview_name, self.duplicate_preview):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.base_url + "/preview/" + name, timeout=3)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()

        self.mutate("restore")
        self.assertEqual(len(self.get_json("/api/inventory")), 2)
        self.assertEqual(self.get_json("/api/excluded"), [])
        with urlopen(self.base_url + "/preview/" + self.preview_name, timeout=3) as response:
            self.assertEqual(response.read(), b"jpeg-test-bytes")
        self.assertFalse(list(self.root.glob(".review-state-*.tmp")))

    def test_exclusion_requires_matching_inventory_index_and_sha(self):
        for index, digest in ((self.index + 2, self.digest), (self.index, "b" * 64)):
            body = json.dumps({"index": index, "sha256": digest}).encode()
            request = Request(self.base_url + "/api/exclude", data=body,
                              headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=3)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
        self.assertEqual(len(self.get_json("/api/inventory")), 2)
        self.assertFalse(server_module.REVIEW_STATE.exists())


if __name__ == "__main__":
    unittest.main()

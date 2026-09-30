#!/usr/bin/env python3
"""Serve the private, metadata-stripped incoming photo review UI on loopback."""

import argparse
import json
import os
import re
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path.home() / "Library" / "Application Support" / "HogMorphStudio" / "incoming-review"
PREVIEWS = ROOT / "previews"
UI_ROOT = Path(__file__).resolve().parents[1] / "tools" / "incoming_review"
ONTOLOGY_PATH = Path(__file__).resolve().parents[1] / "data" / "ontology.json"
REVIEW_STATE = ROOT / "review_state.json"
STATE_LOCK = threading.Lock()
SAFE_IMAGE = re.compile(r"^[0-9]{3}-[0-9a-f]{12}\.jpg$")
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}


def contained_file(path: Path, parent: Path) -> Path:
    """Resolve a regular file beneath parent and reject symlinks/escapes."""
    parent_real = parent.resolve(strict=True)
    if parent.is_symlink() or parent_real != parent.absolute() or path.is_symlink():
        raise ValueError("symlink not allowed")
    resolved = path.resolve(strict=True)
    if parent_real not in resolved.parents or not resolved.is_file():
        raise ValueError("path outside approved directory")
    return resolved


def load_inventory_records():
    if ROOT.is_symlink() or PREVIEWS.is_symlink():
        raise ValueError("review root or previews directory must not be a symlink")
    active = ROOT / "active_inventory.json"
    reviewed = ROOT / "reviewed_inventory.json"
    source = active if active.exists() else reviewed if reviewed.exists() else ROOT / "inventory.json"
    inventory_path = contained_file(source, ROOT)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    records = inventory.get("records")
    if not isinstance(records, list):
        raise ValueError("inventory records must be a list")
    safe_records = []
    for row in records:
        if not isinstance(row, dict):
            continue
        index, digest, triage, preview = row.get("index"), row.get("sha256"), row.get("visual_triage"), row.get("preview")
        if type(index) is not int or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            continue
        if not isinstance(preview, str) or not preview.startswith("previews/"):
            continue
        filename = preview.removeprefix("previews/")
        if not SAFE_IMAGE.fullmatch(filename):
            continue
        # Verify every referenced preview before exposing it to the browser.
        contained_file(PREVIEWS / filename, PREVIEWS)
        # Keep only the human-review candidate pool. In particular, confirmed
        # unrelated species are never exposed, even if an upstream inventory
        # accidentally includes them in its records.
        if triage not in {"candidate_western_hognose", "uncertain"}:
            continue
        safe_records.append({"index": index, "sha256": digest, "visual_triage": triage,
                             "preview_name": filename, "preview_url": f"/preview/{filename}"})
    return safe_records


def read_review_state():
    if REVIEW_STATE.is_symlink():
        raise ValueError("review state must not be a symlink")
    if not REVIEW_STATE.exists():
        return set()
    state_path = contained_file(REVIEW_STATE, ROOT)
    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("excluded"), list):
        raise ValueError("invalid review state")
    excluded = set()
    for entry in data["excluded"]:
        if (not isinstance(entry, dict) or type(entry.get("index")) is not int
                or not isinstance(entry.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise ValueError("invalid exclusion record")
        excluded.add((entry["index"], entry["sha256"]))
    return excluded


def write_review_state(excluded):
    """Atomically update the one fixed server-side state file."""
    if ROOT.is_symlink() or REVIEW_STATE.is_symlink():
        raise ValueError("review root or state file must not be a symlink")
    payload = {"schema_version": 1, "excluded": [
        {"index": index, "sha256": digest}
        for index, digest in sorted(excluded)
    ]}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=ROOT,
                                         prefix=".review-state-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, REVIEW_STATE)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def load_inventory():
    records = load_inventory_records()
    excluded = read_review_state()
    return [{k: v for k, v in row.items() if k != "preview_name"}
            for row in records if (row["index"], row["sha256"]) not in excluded]


def load_excluded():
    records = load_inventory_records()
    excluded = read_review_state()
    return [{k: row[k] for k in ("index", "sha256", "visual_triage")}
            for row in records if (row["index"], row["sha256"]) in excluded]


def validate_record_identity(payload):
    if not isinstance(payload, dict) or type(payload.get("index")) is not int:
        raise ValueError("index and sha256 are required")
    digest = payload.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("index and sha256 are required")
    row = next((r for r in load_inventory_records()
                if r["index"] == payload["index"] and r["sha256"] == digest), None)
    if row is None:
        raise ValueError("index and sha256 do not match a review inventory record")
    return row


def load_ontology():
    data = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    # Expose only vocabulary needed by the form; no paths or other project data.
    return {"traits": [{"id": t["id"], "name_en": t["name_en"], "name_zh": t["name_zh"],
                        "kind": t["kind"], "inheritance": t["inheritance"], "states": t["states"]}
                       for t in data["traits"]],
            "aliases": [{"id": a["id"], "name_en": a["name_en"], "name_zh": a["name_zh"],
                         "components": a["components"]} for a in data["aliases"]]}


class Handler(BaseHTTPRequestHandler):
    server_version = "HogMorphReview/1.0"

    def log_message(self, fmt, *args):
        # URLs are fixed routes; avoid logging any inventory data.
        super().log_message(fmt, *args)

    def send_bytes(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, status=200):
        self.send_bytes(json.dumps(data, separators=(",", ":")).encode(),
                        "application/json; charset=utf-8", status)

    def reject_mutation_origin(self):
        host = self.headers.get("Host", "")
        allowed_host = {f"127.0.0.1:{self.server.server_port}", "127.0.0.1"}
        origin = self.headers.get("Origin")
        return host not in allowed_host or (origin is not None and origin != f"http://127.0.0.1:{self.server.server_port}")

    def read_json_body(self):
        if self.headers.get_content_type() != "application/json":
            raise ValueError("application/json required")
        length = int(self.headers.get("Content-Length", "0"))
        if not 1 <= length <= 2048:
            raise ValueError("invalid request size")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict) or set(value) != {"index", "sha256"}:
            raise ValueError("only index and sha256 are accepted")
        return value

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/inventory":
                self.send_json(load_inventory())
            elif path == "/api/excluded":
                self.send_json(load_excluded())
            elif path == "/api/ontology":
                body = json.dumps(load_ontology(), separators=(",", ":")).encode()
                self.send_bytes(body, "application/json; charset=utf-8")
            elif path.startswith("/preview/"):
                name = path[len("/preview/"):]
                if not SAFE_IMAGE.fullmatch(name):
                    raise ValueError("invalid preview name")
                excluded = read_review_state()
                row = next((r for r in load_inventory_records() if r["preview_name"] == name), None)
                if row is None or (row["index"], row["sha256"]) in excluded:
                    self.send_bytes(b"Preview is not in the active review set", "text/plain; charset=utf-8", 404)
                    return
                preview = contained_file(PREVIEWS / name, PREVIEWS)
                self.send_bytes(preview.read_bytes(), "image/jpeg")
            elif path in {"/", "/index.html", "/identity.js", "/app.js", "/style.css"}:
                name = "index.html" if path in {"/", "/index.html"} else path.lstrip("/")
                file_path = contained_file(UI_ROOT / name, UI_ROOT)
                self.send_bytes(file_path.read_bytes(), MIME[file_path.suffix])
            else:
                self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
        except FileNotFoundError:
            self.send_bytes(b"Incoming review inventory or preview is unavailable", "text/plain; charset=utf-8", 404)
        except (ValueError, json.JSONDecodeError, KeyError, OSError):
            self.send_bytes(b"Incoming review data failed path or schema validation", "text/plain; charset=utf-8", 400)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in {"/api/exclude", "/api/restore"}:
            self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
            return
        if self.reject_mutation_origin():
            self.send_bytes(b"Loopback origin required", "text/plain; charset=utf-8", 403)
            return
        try:
            payload = self.read_json_body()
            with STATE_LOCK:
                row = validate_record_identity(payload)
                excluded = read_review_state()
                digest, index = row["sha256"], row["index"]
                related = {(r["index"], r["sha256"]) for r in load_inventory_records()
                           if r["sha256"] == digest}
                if path == "/api/exclude":
                    excluded.update(related)
                elif (index, digest) in excluded:
                    excluded.difference_update(related)
                else:
                    raise ValueError("record is not excluded")
                write_review_state(excluded)
            self.send_json({"index": index, "sha256": digest,
                            "excluded": path == "/api/exclude"})
        except (ValueError, json.JSONDecodeError, KeyError) as error:
            self.send_bytes(str(error).encode("utf-8"), "text/plain; charset=utf-8", 400)
        except OSError:
            self.send_bytes(b"Review state could not be saved", "text/plain; charset=utf-8", 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    # Deliberately hard-coded: no host, root, or bind-address override exists.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Private review UI: http://127.0.0.1:{args.port} (inventory root is fixed to {ROOT})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

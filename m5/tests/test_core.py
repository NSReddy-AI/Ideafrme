import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from creative_core import (CreativeError, new_document, validate, apply, undo, redo,
                           approve, snapshot, fingerprint, load, save,
                           recover_previous, file_digest)

WORKSPACE = Path(__file__).resolve().parents[1]
RUNTIME = WORKSPACE / ".runtime"


class CoreTests(unittest.TestCase):
    def setUp(self):
        # No default system temp directory; refuse redirected/symlinked runtime roots.
        self.assertEqual(Path.cwd().resolve(), WORKSPACE)
        self.assertTrue(RUNTIME.is_dir())
        self.assertFalse(RUNTIME.is_symlink())
        self.temporary = tempfile.TemporaryDirectory(prefix="case-", dir=RUNTIME)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.doc = new_document()

    def move(self, doc=None, x=90):
        return apply(doc or self.doc, {"op": "move", "element_id": "title", "x": x, "y": 120}, self.root)

    def asset(self):
        path = self.root / "synthetic.svg"
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        return {"id": "synthetic", "path": path.name, "kind": "vector",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_valid_document(self):
        self.assertIs(validate(self.doc, self.root), self.doc)

    def test_save_reopen_fidelity(self):
        doc = snapshot(approve(self.move(), "Human reviewer", self.root), "First", self.root)
        save(doc, self.root)
        self.assertEqual(load(self.root), doc)

    def test_duplicate_ids(self):
        for section in ("elements", "views", "content"):
            with self.subTest(section=section):
                doc = copy.deepcopy(self.doc)
                doc[section].append(copy.deepcopy(doc[section][0]))
                with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_missing_references(self):
        for key in ("view_id", "content_id"):
            with self.subTest(key=key):
                doc = copy.deepcopy(self.doc)
                doc["elements"][0][key] = "missing"
                with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_missing_asset(self):
        self.doc["assets"] = [{"id": "a", "path": "missing.png", "kind": "image"}]
        with self.assertRaises(CreativeError): validate(self.doc, self.root)

    def test_missing_font_and_brand(self):
        for change in ("font", "brand"):
            doc = copy.deepcopy(self.doc)
            if change == "font": doc["elements"][0]["style"]["font_asset_id"] = "missing"
            else: doc["brand"] = {"id": "brand", "asset_id": "missing"}
            with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_unsupported_versions(self):
        for key, value in (("format", "ai-reel-studio/creative@2"), ("schema_version", 2),
                           ("schema_version", True)):
            doc = copy.deepcopy(self.doc)
            doc[key] = value
            with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_invalid_geometry(self):
        for key, value in (("width", 0), ("height", -1), ("x", float("inf")),
                           ("y", float("nan")), ("x", True), ("width", "100")):
            doc = copy.deepcopy(self.doc)
            doc["elements"][0][key] = value
            with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_path_traversal(self):
        for path in ("../escape.svg", "/tmp/escape.svg", "a/../../x", "a\\x", "C:/x",
                     "./x", "a//x", "https://example.com/a"):
            doc = copy.deepcopy(self.doc)
            doc["assets"] = [{"id": "a", "path": path, "kind": "vector"}]
            with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_asset_symlink_escape(self):
        # Escape target is outside this project root but still INSIDE AI Studio.
        target = self.root.parent / (self.root.name + "-external.svg")
        target.write_text("synthetic", encoding="utf-8")
        self.addCleanup(target.unlink)
        (self.root / "link.svg").symlink_to(target)
        self.doc["assets"] = [{"id": "a", "path": "link.svg", "kind": "vector"}]
        with self.assertRaises(CreativeError): validate(self.doc, self.root)

    def test_directory_symlink_escape(self):
        (self.root / "linked").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(CreativeError): save(self.doc, self.root, "linked/file.json")

    def test_root_symlink_rejected(self):
        link = self.root / "root-link"
        link.symlink_to(self.root, target_is_directory=True)
        doc = copy.deepcopy(self.doc)
        doc["assets"] = [self.asset()]
        with self.assertRaises(CreativeError): validate(doc, link)

    def test_malformed_json_and_encoding(self):
        for data in (b"{", b"[]", b"null", b"\xff", b'{"x":NaN}', b'{"x":Infinity}'):
            (self.root / "creative.json").write_bytes(data)
            with self.assertRaises(CreativeError): load(self.root)
            self.assertEqual((self.root / "creative.json").read_bytes(), data)

    def test_duplicate_json_keys_nested(self):
        for data in (b'{"format":1,"format":2}', b'{"nested":{"x":1,"x":2}}'):
            (self.root / "creative.json").write_bytes(data)
            with self.assertRaisesRegex(CreativeError, "duplicate JSON key"): load(self.root)

    def test_undo_redo_100_transactions(self):
        original = fingerprint(self.doc)
        doc = self.doc
        for i in range(100):
            doc = apply(doc, {"op": "move", "element_id": "title", "x": 100 + i, "y": i}, self.root)
        final = fingerprint(doc)
        for _ in range(100): doc = undo(doc, self.root)
        self.assertEqual(fingerprint(doc), original)
        for _ in range(100): doc = redo(doc, self.root)
        self.assertEqual(fingerprint(doc), final)

    def test_all_operations_reversible(self):
        el = {"id": "shape", "type": "shape", "view_id": "portrait", "x": 0,
              "y": 0, "width": 50, "height": 50, "style": {"shape": "ellipse"}}
        operations = [{"op": "add", "element": el},
                      {"op": "move", "element_id": "title", "x": 25, "y": 35},
                      {"op": "restyle", "element_id": "title", "style": {"opacity": 0.5}},
                      {"op": "edit_text", "element_id": "title", "text": "తెలుగు / English"},
                      {"op": "remove", "element_id": "title"}]
        for op in operations:
            with self.subTest(op=op["op"]):
                changed = apply(self.doc, op, self.root)
                self.assertEqual(fingerprint(undo(changed, self.root)), fingerprint(self.doc))
                self.assertEqual(fingerprint(redo(undo(changed, self.root), self.root)), fingerprint(changed))

    def test_failed_operation_no_mutation(self):
        original = copy.deepcopy(self.doc)
        for op in ({"op": "move", "element_id": "title", "x": "bad", "y": 0},
                   {"op": "execute", "command": "anything"},
                   {"op": "restyle", "element_id": "title", "style": {"script": "bad"}},
                   {"op": "remove", "element_id": "missing"}):
            with self.assertRaises(CreativeError): apply(self.doc, op, self.root)
            self.assertEqual(self.doc, original)

    def test_redo_branch_discarded(self):
        doc = undo(self.move(), self.root)
        doc = self.move(doc, x=222)
        self.assertEqual(len(doc["history"]["transactions"]), 1)
        with self.assertRaises(CreativeError): redo(doc, self.root)

    def test_empty_undo_redo(self):
        for action in (undo, redo):
            with self.assertRaises(CreativeError): action(self.doc, self.root)

    def test_approval_invalidation_and_snapshot_preservation(self):
        doc = snapshot(approve(self.doc, "Reviewer", self.root), "Approved original", self.root)
        original_version = copy.deepcopy(doc["versions"][0])
        changed = self.move(doc)
        self.assertEqual(changed["approvals"], [])
        self.assertEqual(changed["versions"][0], original_version)
        changed = approve(changed, "Reviewer", self.root)
        self.assertFalse(undo(changed, self.root)["approvals"])
        self.assertFalse(redo(undo(changed, self.root), self.root)["approvals"])

    def test_stale_approval_rejected(self):
        doc = approve(self.doc, "Reviewer", self.root)
        doc["content"][0]["text"] = "Changed"
        with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_asset_hash_and_approval_pin(self):
        self.doc["assets"] = [self.asset()]
        approve(self.doc, "Reviewer", self.root)
        self.doc["assets"][0]["sha256"] = "0" * 64
        with self.assertRaises(CreativeError): validate(self.doc, self.root)
        del self.doc["assets"][0]["sha256"]
        with self.assertRaises(CreativeError): approve(self.doc, "Reviewer", self.root)

    def test_named_versions_immutable_on_save(self):
        doc = snapshot(self.doc, "Named", self.root)
        save(doc, self.root)
        changed = copy.deepcopy(doc)
        changed["versions"][0]["name"] = "Renamed"
        changed["revision"] += 1
        with self.assertRaises(CreativeError): save(changed, self.root)
        self.assertEqual(load(self.root), doc)
        with self.assertRaises(CreativeError): snapshot(doc, "Named", self.root)

    def test_recover_after_interrupted_save(self):
        save(self.doc, self.root)
        real_replace = os.replace
        def interrupt(source, target):
            if Path(target).name == "creative.json": raise OSError("simulated interruption")
            return real_replace(source, target)
        with patch("creative_core.persistence.os.replace", side_effect=interrupt):
            with self.assertRaises(OSError): save(self.move(), self.root)
        self.assertEqual(load(self.root), self.doc)
        self.assertEqual(recover_previous(self.root), self.doc)
        self.assertEqual(list(self.root.glob(".creative-save-*")), [])

    def test_corrupt_primary_explicit_recovery(self):
        save(self.doc, self.root)
        save(self.move(), self.root)
        (self.root / "creative.json").write_bytes(b"interrupted")
        with self.assertRaises(CreativeError): load(self.root)
        with self.assertRaises(CreativeError): save(self.doc, self.root)
        recovered = recover_previous(self.root)
        self.assertEqual(recovered, self.doc)
        save(recovered, self.root, "recovered.json")
        self.assertEqual((self.root / "creative.json").read_bytes(), b"interrupted")

    def test_invalid_save_preserves_primary_and_backup(self):
        save(self.doc, self.root)
        save(self.move(), self.root)
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        bad = copy.deepcopy(self.doc)
        bad["elements"][0]["width"] = -1
        with self.assertRaises(CreativeError): save(bad, self.root)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_concurrent_change_detection(self):
        digest = save(self.doc, self.root)
        save(self.move(), self.root, expected_digest=digest)
        with self.assertRaises(CreativeError): save(self.move(x=999), self.root, expected_digest=digest)
        self.assertNotEqual(file_digest(self.root), digest)

    def test_save_revision_and_identity_guards(self):
        save(self.doc, self.root)
        for key, value in (("id", "different"), ("revision", -1)):
            changed = copy.deepcopy(self.doc)
            changed[key] = value
            with self.assertRaises(CreativeError): save(changed, self.root)
        changed = copy.deepcopy(self.doc)
        changed["project"]["name"] = "Changed without revision"
        with self.assertRaises(CreativeError): save(changed, self.root)

    def test_approval_without_hash_rejected_on_load(self):
        self.doc["assets"] = [self.asset()]
        doc = approve(self.doc, "Reviewer", self.root)
        del doc["assets"][0]["sha256"]
        doc["approvals"][0]["fingerprint"] = fingerprint(doc)
        with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_interrupted_backup_keeps_last_good_file(self):
        save(self.doc, self.root)
        with patch("creative_core.persistence.os.fsync", side_effect=OSError("disk flush failed")):
            with self.assertRaises(OSError): save(self.move(), self.root)
        self.assertEqual(load(self.root), self.doc)
        self.assertEqual(list(self.root.glob(".creative-save-*")), [])

    def test_snapshot_hash_tamper_rejected(self):
        doc = snapshot(self.doc, "Original", self.root)
        doc["versions"][0]["snapshot"]["project"]["name"] = "Tampered"
        with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_noop_save_preserves_previous_revision(self):
        save(self.doc, self.root)
        moved = self.move()
        save(moved, self.root)
        save(moved, self.root)
        self.assertEqual(recover_previous(self.root), self.doc)

    def test_save_symlink_target_and_backup(self):
        for name in ("creative.json", "creative.json.previous"):
            link = self.root / name
            target = self.root / "unchanged.txt"
            target.write_text("unchanged", encoding="utf-8")
            link.symlink_to(target)
            with self.assertRaises(CreativeError): save(self.doc, self.root)
            self.assertEqual(target.read_text(), "unchanged")
            link.unlink()

    def test_corrupt_history_rejected(self):
        doc = self.move()
        doc["history"]["cursor"] = 0
        with self.assertRaises(CreativeError): validate(doc, self.root)

    def test_claim_quote_edits_blocked(self):
        self.doc["assets"] = [self.asset()]
        for kind in ("claim", "quote"):
            self.doc["content"][0].update(kind=kind, source_ref="synthetic")
            validate(self.doc, self.root)
            with self.assertRaises(CreativeError):
                apply(self.doc, {"op": "edit_text", "element_id": "title", "text": "Changed"}, self.root)

    def test_editable_types(self):
        self.doc["assets"] = [self.asset()]
        vector = {"id": "v", "type": "vector", "view_id": "portrait", "asset_id": "synthetic",
                  "x": 0, "y": 0, "width": 100, "height": 100, "style": {}}
        doc = apply(self.doc, {"op": "add", "element": vector}, self.root)
        save(doc, self.root)
        self.assertEqual(load(self.root)["elements"][-1], vector)
        for kind in ("image", "logo", "video"):
            doc = copy.deepcopy(self.doc)
            doc["assets"][0]["kind"] = kind
            el = dict(vector, id=kind, type=kind)
            validate(apply(doc, {"op": "add", "element": el}, self.root), self.root)

    def test_wrong_types_and_unknown_fields(self):
        for key, value in (("elements", None), ("languages", [{}]), ("revision", True),
                           ("assets", [None]), ("approvals", {})):
            doc = copy.deepcopy(self.doc)
            doc[key] = value
            with self.assertRaises(CreativeError): validate(doc, self.root)
        self.doc["unknown"] = "unsupported"
        with self.assertRaises(CreativeError): validate(self.doc, self.root)


if __name__ == "__main__":
    unittest.main()

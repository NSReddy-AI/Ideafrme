"""New manual-UI tests only; accepted implementation and legacy suites stay untouched."""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import creative_core as core
from studio_manual_ui.service import Studio, UIError, RUNTIME, decode, encoded

ROOT = Path(os.environ["STUDIO_UI_TEST_ROOT"])


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / self._testMethodName
        self.service = Studio(self.root)
        self.addCleanup(self.service.close)
        self.view = self.service.create({"name":"Manual test", "text":"మొదటి పాఠ్యం / First text", "language":"te"})

    def action(self, kind, **fields):
        self.view = self.service.action({"project_id":self.view["project_id"], "expected_revision":self.view["revision"], "action":kind, **fields})
        return self.view

    def test_create_valid_and_no_media(self):
        doc = self.service.document(self.view["project_id"])
        self.assertEqual(core.validate(doc, self.root / "projects" / doc["id"]), doc)
        self.assertEqual(len(doc["content"]), 32)
        self.assertEqual(doc["assets"], [])
        self.assertIsNone(doc["brand"])
        self.assertTrue(self.view["dirty"])
        self.assertFalse(self.view["saved"])

    def test_new_text_has_independent_binding(self):
        initial = self.view["content"][0]["text"]
        self.action("add_text", language="te")
        layer = self.view["elements"][-1]
        self.action("edit_text", element_id=layer["id"], text="స్వతంత్ర పాఠ్యం / independent")
        doc = self.service.document(self.view["project_id"])
        self.assertEqual(doc["content"][0]["text"], initial)
        self.assertNotEqual(layer["content_id"], "headline")

    def test_geometry_and_style_operations(self):
        self.action("add_shape", shape="rectangle"); shape = self.view["elements"][-1]["id"]
        self.action("move", element_id=shape, x=-10, y=200)
        self.action("color", element_id=shape, color="#aBc123")
        self.assertEqual(self.view["elements"][-1]["x"], -10)
        self.assertEqual(self.view["elements"][-1]["style"]["fill"], "#aBc123")
        self.action("add_shape", shape="ellipse")
        self.action("font_size", element_id="title", font_size=96)
        self.assertEqual(self.view["elements"][0]["style"]["font_size"], 96)

    def test_undo_redo_edit_and_add(self):
        self.action("add_text", language="en")
        after_add = copy.deepcopy(self.view["elements"])
        self.action("undo"); self.assertEqual(len(self.view["elements"]), 1)
        self.action("redo"); self.assertEqual(self.view["elements"], after_add)
        self.action("edit_text", element_id="title", text="Edited")
        self.action("undo"); self.assertEqual(self.view["content"][0]["text"], "మొదటి పాఠ్యం / First text")
        self.action("redo"); self.assertEqual(self.view["content"][0]["text"], "Edited")

    def test_save_reopen_preserves_exact_unicode(self):
        for value in ("  తెలుగు\nEnglish \t ", "é / e\u0301 / తెలుగు క్ష్మ", '<img src="https://example.invalid/x" onerror="alert(1)">'):
            self.action("edit_text", element_id="title", text=value)
            self.action("save")
            self.assertFalse(self.view["dirty"])
            self.action("move", element_id="title", x=90, y=120)
            self.view = self.service.reopen(self.view["project_id"], self.view["revision"])
            self.assertEqual(self.view["content"][0]["text"], value)
            self.assertFalse(self.view["dirty"])

    def test_saved_size_limit_includes_core_terminal_newline(self):
        size = len(encoded(self.service.document(self.view["project_id"]))) + 1
        with patch("studio_manual_ui.service.MAX_DOCUMENT", size):
            self.action("save")
            self.view = self.service.reopen(self.view["project_id"], self.view["revision"])
            self.assertFalse(self.view["dirty"])
        path = self.root/"projects"/self.view["project_id"]/"creative.json"
        before = path.read_bytes()
        with patch("studio_manual_ui.service.MAX_DOCUMENT", size-1):
            with self.assertRaises(UIError): self.action("save")
        self.assertEqual(path.read_bytes(), before)

    def test_resume_explicit_and_saved_projects_listed(self):
        self.action("save")
        identity = self.view["project_id"]
        self.service.close()
        with self.assertRaises(FileExistsError): Studio(self.root)
        self.service = Studio(self.root, resume=True)
        self.assertEqual(self.service.list_projects()[0]["project_id"], identity)
        self.assertEqual(self.service.document(identity)["id"], identity)

    def test_no_approval_resurrection(self):
        identity = self.view["project_id"]; directory = self.root/"projects"/identity
        approved = core.approve(self.service.document(identity), "Synthetic test reviewer", directory)
        self.service._working[identity] = approved
        self.view = self.service.view(identity)
        self.action("save")
        self.action("edit_text", element_id="title", text="Different")
        self.assertEqual(self.view["approval_count"], 0)
        self.action("undo"); self.assertEqual(self.view["approval_count"], 0)
        self.action("redo"); self.assertEqual(self.view["approval_count"], 0)
        self.action("save")
        previous = json.loads((directory/"creative.json.previous").read_text())
        self.assertEqual(len(previous["approvals"]), 1)

    def test_conflicting_revision_rejected_without_mutation(self):
        stale = self.view["revision"]
        self.action("move", element_id="title", x=81, y=101)
        before = self.service.document(self.view["project_id"])
        with self.assertRaises(UIError) as error:
            self.service.action({"project_id":self.view["project_id"], "expected_revision":stale,"action":"undo"})
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(before, self.service.document(self.view["project_id"]))

    def test_external_saved_change_not_overwritten(self):
        self.action("save")
        path = self.root/"projects"/self.view["project_id"]/"creative.json"
        doc = json.loads(path.read_text()); doc["revision"] += 1
        path.write_text(json.dumps(doc,ensure_ascii=False))
        before = path.read_bytes()
        with self.assertRaises(UIError) as error: self.action("save")
        self.assertEqual(error.exception.status,409)
        self.assertEqual(path.read_bytes(),before)

    def test_malformed_requests_paths_and_unsupported_actions(self):
        before = self.service.document(self.view["project_id"])
        for value in ("../outside", "/tmp/file", "file:///tmp/a", "..%2foutside", True):
            with self.assertRaises(UIError): self.service.document(value)
        for request in ({"action":"approve"}, {"action":"import"}, {"action":"save","path":"outside"}, [], None):
            with self.assertRaises(UIError): self.service.action(request)
        self.assertEqual(before,self.service.document(self.view["project_id"]))

    def test_invalid_values_and_noop_preserve_state(self):
        before = self.service.document(self.view["project_id"])
        for action, fields in (("edit_text",{"element_id":"title","text":""}),
                               ("edit_text",{"element_id":"title","text":"\ud800"}),
                               ("move",{"element_id":"title","x":True,"y":0}),
                               ("font_size",{"element_id":"title","font_size":0}),
                               ("color",{"element_id":"title","color":"url(https://example.invalid)"}),
                               ("move",{"element_id":"title","x":80,"y":100})):
            with self.assertRaises(UIError): self.action(action,**fields)
        self.assertEqual(before,self.service.document(self.view["project_id"]))

    def test_unknown_fields_and_json_duplicates(self):
        with self.assertRaises(UIError): self.service.create({"name":"A","text":"B","language":"en","path":"a"})
        for raw in (b'{"name":"a","name":"b"}', b'{"x":NaN}', b'\xff', b'{'):
            with self.assertRaises(UIError): decode(raw)

    def test_text_slot_capacity_is_explicit(self):
        for _ in range(15): self.action("add_text",language="te")
        self.assertEqual(self.view["remaining_text_slots"]["te"],0)
        before = self.service.document(self.view["project_id"])
        with self.assertRaises(UIError): self.action("add_text",language="te")
        self.assertEqual(before,self.service.document(self.view["project_id"]))

    def test_unsafe_roots_symlinks_and_hardlinks_rejected(self):
        with self.assertRaises(UIError): Studio(Path.cwd()/"r1_data")
        alias = ROOT / "alias-instance"; alias.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(UIError): Studio(alias,resume=True)
        self.action("save")
        target = self.root/"projects"/self.view["project_id"]/"creative.json"
        os.link(target,self.root/"aliased.json")
        with self.assertRaises(UIError): self.service.reopen(self.view["project_id"])

    def test_saved_media_reference_rejected_before_core_asset_reads(self):
        self.action("save")
        target = self.root/"projects"/self.view["project_id"]/"creative.json"
        doc = self.service.document(self.view["project_id"])
        doc["assets"] = [{"id":"hostile","kind":"image","path":"../outside.png"}]
        target.write_text(json.dumps(doc,ensure_ascii=False))
        with self.assertRaises(UIError) as error: self.service.reopen(self.view["project_id"])
        self.assertEqual(error.exception.code,"unsupported")

    def test_analysis_absence_fault_and_incompatibility_do_not_block_manual_work(self):
        for state in ("ABSENT","DISABLED","FAULTED","INCOMPATIBLE","READY"):
            self.service.analysis_provider = lambda: {"state":state,"real_media_enabled":True,"controls_enabled":True}
            info = self.service.analysis()
            self.assertEqual(info["state"],state)
            self.assertFalse(info["real_media_enabled"])
            self.assertFalse(info["controls_enabled"])
            self.action("move",element_id="title",x=self.view["revision"]+100,y=200)
            self.action("save")
        def broken(): raise RuntimeError("private diagnostic must not leak")
        self.service.analysis_provider = broken
        self.assertEqual(self.service.analysis()["error"],"status-unavailable")
        self.action("move",element_id="title",x=999,y=200)

    def test_detached_document_and_status_projections(self):
        doc = self.service.document(self.view["project_id"]); doc["content"][0]["text"]="forged"
        view = self.service.view(self.view["project_id"]); view["elements"][0]["x"]=500
        self.assertNotEqual(self.service.document(self.view["project_id"])["content"][0]["text"],"forged")
        self.assertEqual(self.service.view(self.view["project_id"])["elements"][0]["x"],80)

    def test_second_owner_refused(self):
        with self.assertRaises(UIError): Studio(self.root,resume=True)

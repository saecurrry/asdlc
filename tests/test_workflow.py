import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema.exceptions import ValidationError
from asdlc.adapters import FakeAdapter, envelope
from asdlc.engine import Engine, initial
from asdlc.store import GateError, Store, atomic, validate
from examples.demo import demonstrate


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        local = Path(".asdlc-local/tests")
        local.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=local)
        self.wiki = Path(self.tmp.name)
        self.target = Path.cwd()
        self.store = Store(self.wiki, "p1")
        self.store.create(initial("p1", self.target, self.wiki, True, "Fixture problem"))
        self.engine = Engine(self.store)
        self.fake = FakeAdapter()

    def tearDown(self):
        self.tmp.cleanup()

    def rev(self): return self.store.load()["revision"]

    def worker(self, content="# brief"):
        d = self.engine.dispatch(self.rev(), "worker", "author")
        return self.engine.submit(self.fake.worker(d, content))

    def review(self, findings=None):
        d = self.engine.dispatch(self.rev(), "review", "independent")
        return self.engine.submit(self.fake.reviewer(d, findings))

    def test_end_to_end_fixture_new_process(self):
        events, state = demonstrate(self.wiki, self.target, "demo")
        self.assertEqual(state["status"], "stale")
        self.assertFalse(state["approvals"][0]["valid"])
        self.assertEqual(len(events), 8)
        self.assertTrue((self.wiki / "projects/demo/raid.md").exists())

    def test_schema_revision_and_identity(self):
        with self.assertRaises(ValidationError):
            validate("project-state", {"project": "invalid"})
        self.engine.start(0)
        with self.assertRaises(GateError):
            self.engine.start(0)
        d = self.engine.dispatch(self.rev(), "worker", "author")
        forged = self.fake.worker(d, "brief")
        forged["actor"] = "intruder"
        with self.assertRaises(GateError):
            self.engine.submit(forged)
        self.engine.submit(self.fake.worker(d, "brief"))
        with self.assertRaises(GateError):
            self.engine.dispatch(self.rev(), "review", "author")

    def test_two_repairs_then_block_no_pass(self):
        self.engine.start(0)
        finding = dict(id="F", severity="high", blocking=True, location="brief", evidence="Missing metric", criterion="Measurable", impact="Untestable", resolution="Add metric", owner="discovery", disposition="open")
        for count in range(3):
            self.worker(f"brief {count}")
            self.review([finding])
        self.assertEqual(self.store.load()["repairs"], 2)
        self.assertEqual(self.store.load()["status"], "blocked")
        with self.assertRaises(GateError):
            self.engine.dispatch(self.rev(), "worker", "author")
        with self.assertRaises(GateError):
            self.engine.approve(self.rev(), self.store.load()["artifact"]["hash"], "human")

    def test_pass_cannot_hide_blocking_finding(self):
        self.engine.start(0)
        self.worker()
        d = self.engine.dispatch(self.rev(), "review", "independent")
        f = dict(id="F", severity="high", blocking=True, location="brief", evidence="Gap", criterion="Required", impact="Blocks", resolution="Fix", owner="discovery", disposition="open")
        with self.assertRaises(GateError):
            self.engine.submit(envelope(d, verdict="pass", findings=[f]))
        self.assertEqual(self.store.load()["status"], "in_review")

    def test_missing_human_decision_resume(self):
        self.engine.start(0)
        self.worker()
        d = self.engine.dispatch(self.rev(), "review", "independent")
        q = dict(id="Q", text="Scope?", blocking=True, answer=None)
        self.engine.submit(envelope(d, verdict="needs_human_decision", questions=[q]))
        self.assertEqual(Store(self.wiki, "p1").resume()["status"], "awaiting_input")
        with self.assertRaises(GateError):
            self.engine.dispatch(self.rev(), "worker", "author")
        self.engine.answer(self.rev(), "Q", "Email only", "human")
        self.assertEqual(self.store.load()["status"], "running")
        self.assertEqual(len(self.store.load()["decisions"]), 1)
        self.assertEqual(self.store.load()["raid"][0]["status"], "closed")

    def test_blocking_findings_maintain_raid_until_pass(self):
        self.engine.start(0)
        self.worker()
        f = dict(id="F-raid", severity="high", blocking=True, location="brief", evidence="Gap", criterion="Required", impact="Blocks", resolution="Fix", owner="discovery", disposition="open")
        self.review([f])
        self.assertEqual(self.store.load()["raid"][0]["status"], "open")
        self.worker("Fixed brief")
        self.review()
        self.assertEqual(self.store.load()["raid"][0]["status"], "closed")

    def test_changed_answer_invalidates_review_and_old_result(self):
        self.engine.start(0)
        d = self.engine.dispatch(self.rev(), "worker", "author")
        old = self.fake.worker(d, "brief")
        self.engine.question(self.rev(), dict(id="Q", text="Scope?", blocking=True, answer=None))
        with self.assertRaises(GateError):
            self.engine.submit(old)
        self.engine.answer(self.rev(), "Q", "One queue", "human")
        self.worker()
        self.review()
        h = self.store.load()["artifact"]["hash"]
        self.engine.approve(self.rev(), h, "human")
        self.engine.answer(self.rev(), "Q", "Two queues", "human")
        self.assertIsNone(self.store.load()["review"])
        self.assertFalse(self.store.load()["approvals"][0]["valid"])

    def test_worker_cannot_invent_answer(self):
        self.engine.start(0)
        d = self.engine.dispatch(self.rev(), "worker", "author")
        result = self.fake.worker(d, "brief")
        result["questions"] = [dict(id="Q", text="Who?", blocking=True, answer="Invented")]
        with self.assertRaises(GateError):
            self.engine.submit(result)

    def test_direct_question_cannot_invent_answer(self):
        with self.assertRaises(GateError):
            self.engine.question(self.rev(), dict(id="Q", text="Who?", blocking=True, answer="Invented"))
        self.assertEqual(self.rev(), 0)

    def test_changed_artifact_cannot_retain_review_hash(self):
        self.engine.start(0)
        self.worker()
        self.review()
        s = self.store.load()
        old_hash = s["artifact"]["hash"]
        s["artifact"]["content"] = "Tampered brief"
        self.store.path.write_text(json.dumps(s))
        with self.assertRaisesRegex(GateError, "digest mismatch"):
            self.store.resume()
        with self.assertRaises(GateError):
            self.engine.approve(s["revision"], old_hash, "human")

    def test_questions_cannot_reset_correction_budget(self):
        self.engine.start(0)
        f = dict(id="F", severity="high", blocking=True, location="brief", evidence="Gap", criterion="Required", impact="Blocks", resolution="Fix", owner="discovery", disposition="open")
        for count in range(3):
            self.worker(f"brief {count}")
            d = self.engine.dispatch(self.rev(), "review", "independent")
            q = dict(id=f"Q{count}", text="Optional clarification?", blocking=False, answer=None)
            self.engine.submit(envelope(d, verdict="changes_required", findings=[f], questions=[q]))
        self.assertEqual(self.store.load()["repairs"], 2)
        self.assertEqual(self.store.load()["status"], "blocked")
        with self.assertRaises(GateError):
            self.engine.dispatch(self.rev(), "worker", "author")

    def test_correction_adapter_receives_historical_findings(self):
        from asdlc.adapters import CodexAdapter
        self.engine.start(0)
        self.worker("Prior draft missing metric")
        d = self.engine.dispatch(self.rev(), "review", "independent")
        f = dict(id="F-context", severity="high", blocking=True, location="brief", evidence="Metric absent", criterion="Measurable", impact="Untestable", resolution="Add metric", owner="discovery", disposition="open")
        q = dict(id="Q-context", text="Optional?", blocking=False, answer=None)
        self.engine.submit(envelope(d, verdict="changes_required", findings=[f], questions=[q]))
        d = self.engine.dispatch(self.rev(), "worker", "author")
        adapter = object.__new__(CodexAdapter)
        with patch.object(adapter, "run", return_value=self.fake.worker(d, "Corrected metric")) as run:
            adapter.stage(d, self.store.load(), Path("prompts"))
        prompt = run.call_args.args[0]
        self.assertIn("F-context", prompt)
        self.assertIn("Prior draft missing metric", prompt)
        self.assertIn("stale evidence, never an approval", prompt)

    def test_records_and_raid_views(self):
        from asdlc.engine import now
        r = dict(id="R1", kind="risk", owner="owner", source="discovery", impact="Delay", response="Ask owner", status="open", created=now(), updated=now())
        self.engine.record(self.rev(), "raid", r)
        self.engine.raid_status(self.rev(), "R1", "closed")
        self.assertIn("closed", (self.store.folder / "raid.md").read_text())
        link = dict(outcome="O1", requirement="R10", epic="E1", story="S02", test="test_records_and_raid_views", code_change="fixture hash")
        self.engine.record(self.rev(), "traceability", link)
        with self.assertRaises(GateError):
            self.engine.record(self.rev(), "traceability", link)

    def test_worker_raid_proposals_update_stable_record(self):
        from asdlc.engine import now
        self.engine.start(0)
        r = dict(id="risk-1", kind="risk", owner="owner", source="discovery", impact="Delay", response="Ask owner", status="open", created=now(), updated=now())
        self.engine.record(self.rev(), "raid", r)
        d = self.engine.dispatch(self.rev(), "worker", "author")
        proposal = dict(r, impact="Updated impact", created="must not overwrite")
        result = self.fake.worker(d, "brief")
        result["raid"] = [proposal]
        self.engine.submit(result)
        applied = self.store.load()["raid"][0]
        self.assertEqual(applied["impact"], "Updated impact")
        self.assertEqual(applied["created"], r["created"])

    def test_wiki_resource_change_invalidates_approval_on_resume(self):
        self.engine.start(0)
        self.worker()
        self.review()
        s = self.store.load()
        self.engine.approve(s["revision"], s["artifact"]["hash"], "human")
        standards = self.wiki / "standards"
        standards.mkdir()
        (standards / "security.md").write_text("New required security standard")
        resumed = self.store.resume()
        self.assertEqual(resumed["status"], "stale")
        self.assertFalse(resumed["approvals"][0]["valid"])
        self.assertIn("security.md", resumed["inputs"]["resources"][0]["path"])

    def test_atomic_failure_preserves_state(self):
        before = self.store.path.read_bytes()
        with patch("asdlc.store.os.replace", side_effect=OSError("interruption")):
            with self.assertRaises(OSError):
                self.engine.start(0)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertFalse(list(self.store.folder.glob(".asdlc-*")))
        self.assertEqual(self.store.load()["revision"], 0)

    def test_render_failure_recovers_committed_state(self):
        with patch.object(self.store, "views", side_effect=OSError("render interruption")):
            with self.assertRaises(OSError):
                self.engine.start(0)
        self.assertEqual(self.store.load()["status"], "running")
        self.assertEqual(self.store.resume()["revision"], 1)

    def test_nonfixture_requires_separate_repository(self):
        with self.assertRaisesRegex(GateError, "separate Git"):
            initial("live", self.target, self.target, False, "Business intent")

    def test_process_lock_and_project_isolation(self):
        other = Store(self.wiki, "p2")
        other.create(initial("p2", self.target, self.wiki, True, "Other"))
        script = "from asdlc.store import Store; import sys; s=Store(sys.argv[1],'p1'); s.resume()"
        import sys
        with self.store.lock():
            proc = subprocess.run([sys.executable, "-c", script, str(self.wiki)], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("locked", proc.stderr)
            self.engine = Engine(other)
            self.engine.start(0)
        self.assertEqual(self.store.load()["revision"], 0)
        self.assertEqual(other.load()["revision"], 1)
        with self.assertRaises(GateError):
            Store(self.wiki, "../escape")

    def test_corrupt_state_refused_and_views_recovered(self):
        (self.store.folder / "project-status.md").unlink()
        self.store.resume()
        self.assertTrue((self.store.folder / "project-status.md").exists())
        self.store.path.write_text("{}")
        with self.assertRaises(ValidationError):
            self.store.resume()


if __name__ == "__main__":
    unittest.main()

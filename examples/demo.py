"""Synthetic end-to-end discovery demonstration; never grants real project approval."""
import json
import subprocess
import sys
from pathlib import Path

from asdlc.adapters import FakeAdapter
from asdlc.engine import Engine, initial, now
from asdlc.store import GateError, Store


def demonstrate(wiki, target, project="discovery-demo"):
    store = Store(wiki, project)
    store.create(initial(project, target, wiki, True, "FIXTURE: reduce support queue delays"))
    engine, fake, events = Engine(store), FakeAdapter(), []
    def rev(): return store.load()["revision"]
    engine.start(rev())
    engine.question(rev(), dict(id="Q1", text="What is the measurable outcome?", blocking=True, answer=None))
    events.append("Paused awaiting missing business input")
    engine.answer(rev(), "Q1", "FIXTURE human: halve median queue wait within three months", "fixture-human")
    d = engine.dispatch(rev(), "worker", "fixture-author")
    engine.submit(fake.worker(d, "# Draft brief\nReduce queue delays. Success metric not yet included."))
    d = engine.dispatch(rev(), "review", "fixture-reviewer")
    finding = dict(id="F1", severity="high", blocking=True, location="brief", evidence="Success metric absent", criterion="Measurable outcome", impact="Success cannot be tested", resolution="Include approved metric", owner="discovery", disposition="open")
    raid = dict(id="I1", kind="issue", owner="discovery", source="F1", impact="Unverifiable outcome", response="Repair brief and re-review", status="open", created=now(), updated=now())
    result = fake.reviewer(d, [finding])
    result["raid"] = [raid]
    engine.submit(result)
    events.append("Blocking synthetic challenge returned to discovery")
    d = engine.dispatch(rev(), "worker", "fixture-author")
    corrected = fake.worker(d, "# Fixture brief\nOutcome: halve median queue wait within three months.\nScope: queue triage; exclude staffing changes.\nActors: support manager and agents.\nUnconfirmed assumption: instrumented queue available.")
    engine.submit(corrected)
    try:
        engine.submit(corrected)
    except GateError:
        events.append("Duplicate result rejected")
    d = engine.dispatch(rev(), "review", "fixture-reviewer")
    engine.submit(fake.reviewer(d))
    engine.raid_status(rev(), "I1", "closed")
    events.append("Paused for explicit fixture human approval")
    # A separate Python process proves resume does not rely on object/chat memory.
    process = subprocess.run([sys.executable, "-m", "asdlc", "--wiki", str(wiki), "--project", project, "resume"], capture_output=True, text=True, check=True)
    resumed = json.loads(process.stdout)
    assert resumed["status"] == "awaiting_approval"
    events.append("New process resumed exact awaiting-approval state")
    old_hash = resumed["artifact"]["hash"]
    try:
        engine.approve(rev(), "0" * 64, "fixture-human")
    except GateError:
        events.append("Wrong-hash approval rejected")
    engine.approve(rev(), old_hash, "fixture-human")
    events.append("Explicit synthetic approval recorded; no downstream delivery")
    engine.inputs(rev(), "FIXTURE changed scope: email queue only")
    try:
        engine.approve(rev(), old_hash, "fixture-human")
    except GateError:
        events.append("Changed input invalidated approval; stale approval rejected")
    return events, store.load()


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "discovery-demo"
    events, state = demonstrate(Path(".asdlc-local/wiki").resolve(), Path.cwd(), project)
    print(json.dumps(dict(events=events, revision=state["revision"], status=state["status"], synthetic=True), indent=2))

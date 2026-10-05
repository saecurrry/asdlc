"""Real fresh Codex challenge of a synthetic artifact, no human approval."""
import json
import sys
from pathlib import Path
from asdlc.adapters import CodexAdapter, FakeAdapter
from asdlc.engine import Engine, initial
from asdlc.store import Store


if __name__ == "__main__":
    root = Path.cwd()
    project = sys.argv[1] if len(sys.argv) > 1 else "real-review-fixture"
    store = Store(root / ".asdlc-local/wiki", project)
    store.create(initial(project, root, store.wiki, True, "FIXTURE facts agreed by synthetic owner: support agents triage email tickets; reduce median email queue wait from 8 hours to 4 within three months; baseline instrumented queue already exists; scope queue triage, exclude staffing and other channels. No real business facts or human approvals."))
    engine = Engine(store)
    engine.start(0)
    d = engine.dispatch(1, "worker", "fixture-author")
    engine.submit(FakeAdapter().worker(d, "# Synthetic discovery brief\n\nOutcome O1: reduce median email ticket queue wait from 8 hours to 4 hours within three months, using existing instrumented queue timestamps; support manager measures weekly.\n\nActors: support agents and support manager. Scope: email queue triage. Exclusions: staffing changes and other channels. Unknowns: proposed triage approach to be determined in later design; no approach agreed. Risks: prioritisation can delay low priority tickets, requiring fairness measures in BRD. Standards and patterns: no central wiki configured; labelled local fixture only. No real project acceptance."))
    d = engine.dispatch(store.load()["revision"], "review", "fresh-codex-reviewer")
    result = CodexAdapter().stage(d, store.load(), root / "prompts")
    state = engine.submit(result)
    folder = root / "planning/evidence"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "real-fixture-review.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(dict(verdict=result["verdict"], status=state["status"], artifact_hash=d["artifact_hash"], findings=result["findings"], questions=result["questions"]), indent=2))

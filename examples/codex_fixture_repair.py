"""Continue a real fixture challenge with a real owning worker and fresh review."""
import json
import sys
from pathlib import Path
from asdlc.adapters import CodexAdapter
from asdlc.engine import Engine
from asdlc.store import Store


if __name__ == "__main__":
    root = Path.cwd()
    project = sys.argv[1] if len(sys.argv) > 1 else "real-review-current"
    store = Store(root / ".asdlc-local/wiki", project)
    engine, adapter = Engine(store), CodexAdapter()
    d = engine.dispatch(store.load()["revision"], "worker", "fixture-author")
    worker = adapter.stage(d, store.load(), root / "prompts")
    engine.submit(worker)
    (root / "planning/evidence/real-fixture-worker.json").write_text(json.dumps(worker, indent=2), encoding="utf-8")
    if store.load()["status"] != "in_review":
        print(json.dumps({"status": store.load()["status"], "worker": worker}, indent=2))
    else:
        d = engine.dispatch(store.load()["revision"], "review", "fresh-codex-reviewer")
        review = adapter.stage(d, store.load(), root / "prompts")
        state = engine.submit(review)
        (root / "planning/evidence/real-fixture-correction.json").write_text(json.dumps({"worker": worker, "review": review}, indent=2), encoding="utf-8")
        print(json.dumps({"status": state["status"], "verdict": review["verdict"], "findings": review["findings"], "questions": review["questions"]}, indent=2))

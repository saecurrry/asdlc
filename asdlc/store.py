import contextlib
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


class GateError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def resources(wiki):
    wiki = Path(wiki)
    records = []
    for name in ("standards", "patterns"):
        folder = wiki / name
        for path in sorted(folder.rglob("*.md")) if folder.exists() else []:
            content = path.read_text(encoding="utf-8")
            records.append(dict(path=path.relative_to(wiki).as_posix(), content=content, hash=digest(content)))
    return records


def validate(name, value):
    schema = json.loads((Path(__file__).parent / "schemas" / (name + ".json")).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(value)


def integrity(state):
    """Refuse edited sources/evidence without matching canonical provenance."""
    if state["input_hash"] != digest({"inputs": state["inputs"], "questions": state["questions"]}):
        raise GateError("Canonical input digest mismatch")
    for resource in state["inputs"]["resources"]:
        if resource["hash"] != digest(resource["content"]):
            raise GateError("Resource digest mismatch")
    for artifact in state["artifacts"] + ([state["artifact"]] if state["artifact"] else []):
        if artifact["hash"] != digest(artifact["content"]):
            raise GateError("Artifact content digest mismatch")
        source = next((r for r in state["results"] if r["run_id"] == artifact["run_id"]), None)
        if not source or source["kind"] != "worker" or source["content"] != artifact["content"] or source["actor"] != artifact["owner"] or source["input_hash"] != artifact["input_hash"]:
            raise GateError("Artifact provenance mismatch")
    for review in state["reviews"] + ([state["review"]] if state["review"] else []):
        source = next((r for r in state["results"] if r["run_id"] == review["run_id"]), None)
        artifact = next((a for a in state["artifacts"] if a["hash"] == review["artifact_hash"] and a["input_hash"] == source["input_hash"]), None) if source else None
        if not source or not artifact or source["kind"] != "review" or source["actor"] == artifact["owner"] or any(review[k] != source[k] for k in ["actor", "artifact_hash", "verdict", "findings"]):
            raise GateError("Review provenance mismatch")
    if state["artifact"] and state["artifact"]["input_hash"] != state["input_hash"]:
        raise GateError("Current artifact has stale inputs")
    for approval in state["approvals"]:
        if approval["valid"]:
            artifact, review = state["artifact"], state["review"]
            if not artifact or not review or review["verdict"] != "pass" or approval["artifact_hash"] != artifact["hash"] or review["artifact_hash"] != artifact["hash"] or approval["input_hash"] != state["input_hash"]:
                raise GateError("Approval provenance mismatch")
    if state["status"] in ("awaiting_approval", "approved"):
        if not state["artifact"] or not state["review"] or state["review"]["verdict"] != "pass" or any(q["blocking"] and not q["answer"] for q in state["questions"]):
            raise GateError("Canonical gate integrity mismatch")
    if state["status"] == "approved" and not any(a["valid"] for a in state["approvals"]):
        raise GateError("Approved state lacks human approval")


def atomic(path, text):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix=".asdlc-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Store:
    def __init__(self, wiki, project):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", project):
            raise GateError("Unsafe project ID")
        self.wiki = Path(wiki).resolve()
        self.folder = self.wiki / "projects" / project
        self.path = self.folder / "state.json"

    @contextlib.contextmanager
    def lock(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        with (self.folder / ".lock").open("a+b") as stream:
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise GateError("Project is locked by another writer; retry later") from exc
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)

    def load(self):
        state = json.loads(self.path.read_text(encoding="utf-8"))
        validate("project-state", state)
        integrity(state)
        return state

    def create(self, state):
        with self.lock():
            if self.path.exists():
                raise GateError("Project already exists")
            self.save(state)

    def save(self, state):
        validate("project-state", state)
        integrity(state)
        atomic(self.path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
        self.views(state)

    def update(self, revision, action):
        with self.lock():
            state = self.load()
            if self.refresh_resources(state):
                raise GateError("Wiki inputs changed; outputs invalidated. Reload state before continuing")
            if revision != state["revision"]:
                raise GateError("Stale state revision; reload and redispatch")
            action(state)
            state["revision"] += 1
            self.save(state)
            return state

    def resume(self):
        with self.lock():
            state = self.load()
            self.refresh_resources(state)
            self.views(state)
            return state

    def refresh_resources(self, state):
        current = resources(self.wiki)
        if current == state["inputs"]["resources"]:
            return False
        from .engine import Engine
        state["inputs"]["resources"] = current
        Engine.invalidate(state)
        state["revision"] += 1
        self.save(state)
        return True

    def views(self, state):
        next_action = {"not_started": "start discovery", "running": "dispatch worker", "awaiting_input": "answer blocking questions",
                       "in_review": "dispatch independent reviewer", "changes_requested": "dispatch correction worker", "awaiting_approval": "human approval of current artifact hash",
                       "approved": "discovery approved; later stage runtime not implemented", "blocked": "human intervention; resolve material blockers", "stale": "restart discovery for changed inputs"}[state["status"]]
        text = f"# {state['project']} status\n\nGenerated by ASDLC; edit canonical records through CLI.\n\n{'LOCAL FIXTURE — no wiki remote configured' if state['config']['fixture'] else 'Configured local wiki clone'}\n\nRevision: {state['revision']}\nStage: discovery\nStatus: {state['status']}\nNext action: {next_action}\nRepairs: {state['repairs']}/2\n\n[Canonical state](state.json) · [RAID](raid.md)\n\n"
        for q in state["questions"]:
            text += f"- {q['id']}: {q['text']} — {q['answer'] or 'UNANSWERED'}\n"
        if state["artifact"]:
            text += f"\nArtifact SHA256: {state['artifact']['hash']}\n\n{state['artifact']['content']}\n"
        if state["review"]:
            text += f"\nReview: {state['review']['verdict']} ({state['review']['actor']})\n"
            for finding in state["review"]["findings"]:
                text += f"- {finding['id']}: {finding['impact']}; {finding['resolution']}\n"
        atomic(self.folder / "project-status.md", text)
        raid = "# RAID\n\nGenerated by ASDLC from [canonical state](state.json).\n\n"
        for r in state["raid"]:
            raid += f"## {r['id']} — {r['kind']} ({r['status']})\n\nOwner: {r['owner']}\nSource: {r['source']}\nImpact: {r['impact']}\nResponse: {r['response']}\nCreated: {r['created']}\nUpdated: {r['updated']}\n\n"
        atomic(self.folder / "raid.md", raid)

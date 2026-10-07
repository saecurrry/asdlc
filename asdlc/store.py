import contextlib
import hashlib
import json
import os
import re
import tempfile
import time
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
    from .pipeline import input_digest
    if state["input_hash"] != input_digest(state):
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
    if state["schema_version"] == 2 and state["stage"] in ("development", "testing", "sprint-review") and state["artifact"]:
        run_ids = [state["artifact"]["run_id"]] + ([state["review"]["run_id"]] if state["review"] else [])
        for run_id in run_ids:
            result = next(r for r in state["results"] if r["run_id"] == run_id)
            if result.get("code_version") != state["code_version"]:
                raise GateError("Delivery artifact/review code provenance mismatch")
    for approval in state["approvals"]:
        if approval["valid"]:
            artifact, review = state["artifact"], state["review"]
            if not artifact or not review or review["verdict"] != "pass" or approval["artifact_hash"] != artifact["hash"] or review["artifact_hash"] != artifact["hash"] or approval["input_hash"] != state["input_hash"]:
                raise GateError("Approval provenance mismatch")
    if state["status"] in ("awaiting_approval", "approved"):
        if state.get("human_changes_pending", False):
            raise GateError("Human correction request has not received fresh independent pass")
        if not state["artifact"] or not state["review"] or state["review"]["verdict"] != "pass" or any(q["blocking"] and not q["answer"] for q in state["questions"]):
            raise GateError("Canonical gate integrity mismatch")
    if state["status"] == "approved" and not any(a["valid"] for a in state["approvals"]):
        raise GateError("Approved state lacks human approval")
    if state["schema_version"] == 2 and "stage_records" in state:
        if len({r["id"] for r in state["raid"]}) != len(state["raid"]):
            raise GateError("Duplicate canonical RAID IDs")
        from .pipeline import check_pipeline
        check_pipeline(state, integrity)


def replace_file(source, target):
    # Windows scanners can briefly hold generated files. Keep replacement atomic
    # and bounded; persistent permission errors still fail with recovery intact.
    for delay in (0.02, 0.05, 0.1, 0.2, None):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if delay is None:
                raise
            time.sleep(delay)


def atomic(path, text):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix=".asdlc-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        replace_file(temp, path)
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
        validate("pipeline-state" if state.get("schema_version") == 2 else "project-state", state)
        integrity(state)
        if state["schema_version"] == 2:
            self.verify_materialized(state)
        return state

    def verify_materialized(self, state):
        from .pipeline import ARTIFACTS
        for snapshot in [r["state"] for r in state["stage_records"]] + [state]:
            for artifact in snapshot["artifacts"]:
                rel = Path(ARTIFACTS[snapshot["stage"]])
                path = self.folder / rel.parent / (rel.stem + "-" + artifact["hash"] + ".md")
                if path.exists() and path.read_text(encoding="utf-8") != artifact["content"] + "\n":
                    raise GateError("Versioned artifact changed; archive edited file before regeneration")
                from .artifacts import entries, relative
                for item in entries(artifact['content']):
                    rel = Path(relative(item))
                    version = self.folder / rel.parent / (rel.stem + '-' + digest(item['content']) + '.md')
                    if version.exists() and version.read_text(encoding='utf-8') != item['content'] + '\n':
                        raise GateError('Versioned individual artifact changed')

    def create(self, state):
        with self.lock():
            if self.path.exists():
                raise GateError("Project already exists")
            if state["schema_version"] == 2 and any(p.name != ".lock" for p in self.folder.iterdir()):
                raise GateError("Project folder already contains documents; preserve them before authorised init")
            self.save(state)

    def save(self, state):
        validate("pipeline-state" if state.get("schema_version") == 2 else "project-state", state)
        integrity(state)
        atomic(self.path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
        self.views(state)

    def update(self, revision, action, on_failure=None):
        with self.lock():
            state = self.load()
            if self.refresh_resources(state):
                raise GateError("Wiki inputs changed; outputs invalidated. Reload state before continuing")
            if self.refresh_code(state):
                raise GateError("Application code changed; affected delivery gates invalidated. Reload before continuing")
            if revision != state["revision"]:
                raise GateError("Stale state revision; reload and redispatch")
            try:
                action(state)
                state["revision"] += 1
                self.save(state)
            except Exception as exc:
                if on_failure is not None:
                    on_failure(exc)
                raise
            return state

    def resume(self):
        with self.lock():
            state = self.load()
            self.refresh_resources(state)
            self.refresh_code(state)
            self.views(state)
            return state

    def refresh_code(self, state):
        from .code_version import refresh
        if not refresh(state):
            return False
        state["revision"] += 1
        self.save(state)
        return True

    def refresh_resources(self, state):
        current = resources(self.wiki)
        if current == state["inputs"]["resources"]:
            return False
        from .engine import Engine
        if state["schema_version"] == 2:
            from .pipeline import archive_current
            archive_current(state)
        state["inputs"]["resources"] = current
        Engine.invalidate(state, reset_repairs=state["schema_version"] == 2)
        state["revision"] += 1
        self.save(state)
        return True

    def views(self, state):
        next_action = {"not_started": "start discovery", "running": "dispatch worker", "awaiting_input": "answer blocking questions",
                       "in_review": "dispatch independent reviewer", "changes_requested": "dispatch correction worker", "awaiting_approval": "human approval of current artifact hash",
                       "approved": "discovery approved; later stage runtime not implemented", "blocked": "human intervention; resolve material blockers", "stale": "restart discovery for changed inputs"}[state["status"]]
        if state["schema_version"] == 2:
            next_action = {"not_started": "start discovery", "stale": "restart discovery for changed inputs", "approved": "sprint accepted; prepare separately authorised next sprint"}.get(state["status"], next_action)
        if state["dispatch"]:
            next_action = f"await {state['dispatch']['kind']} result for dispatch {state['dispatch']['id']} from {state['dispatch']['actor']}"
            attempts = self.folder / 'attempts'
            if attempts.exists():
                rejected = [p for p in attempts.glob('rejected-*.json') if json.loads(p.read_text(encoding='utf-8'))['result']['run_id'] == state['dispatch']['id']]
                if rejected:
                    latest = max(rejected, key=lambda p: p.stat().st_mtime_ns)
                    next_action += f"; prior result rejected — inspect [retained attempt](attempts/{latest.name}) before retry"
        waiting = state["status"] in ("awaiting_input", "awaiting_approval")
        blocked = state["status"] == "blocked"
        headline = "Waiting on you" if waiting else "Blocked — intervention required" if blocked else "Agent can proceed" if state["status"] != "approved" else "Stage approved"
        text = f"# {state['project']} status\n\n## {headline}\n\n**Waiting on you? {'Yes' if waiting else 'Intervention needed' if blocked else 'No current request'}.**\n\n"
        if state["status"] == "awaiting_input":
            text += "**Your action:** answer the blocking questions below. The agent cannot advance without these answers.\n\n"
            for q in state["questions"]:
                if q["blocking"] and not q["answer"]:
                    text += f"- **{q['id']}: {q['text']}**\n"
        elif state["status"] == "awaiting_approval":
            text += f"**Your action:** approve or reject this independently reviewed {state['stage']} artifact.\n\nExact artifact hash: `{state['artifact']['hash']}`.\nExpected state revision: {state['revision']}.\n\n"
        elif blocked:
            text += "**Required intervention:** review the blocking findings and repair history below; resolve or explicitly change the scope through the orchestrator. Exhaustion has not passed the stage.\n\n"
        else:
            text += f"**Next agent action:** {next_action}.\n\n"
        text += f"Generated by ASDLC; edit canonical records through CLI.\n\n{'LOCAL FIXTURE — no wiki remote configured' if state['config']['fixture'] else 'Configured local wiki clone'}\n\nRevision: {state['revision']}\nStage: {state['stage']}\nStatus: {state['status']}\nNext action: {next_action}\nRepairs: {state['repairs']}/{state.get('repair_limit', 2)}\n\n[Canonical state](state.json) · [RAID](raid.md)\n\n"
        if state["schema_version"] == 2:
            from .pipeline import STAGES, ARTIFACTS
            text += "## Stage gates and handoffs\n\n| Stage | Status | Artifact | Outstanding action |\n|---|---|---|---|\n"
            accepted = {r["state"]["stage"] for r in state["stage_records"] if r["valid"]}
            for stage in STAGES:
                stage_status = "approved" if stage in accepted else state["status"] if stage == state["stage"] else "not started"
                produced = (self.folder / ARTIFACTS[stage]).exists() or stage in accepted or (stage == state["stage"] and state["artifact"])
                artifact_label = f"[{ARTIFACTS[stage]}]({ARTIFACTS[stage]})" if produced else f"`{ARTIFACTS[stage]}` (not yet produced)"
                if produced and stage not in accepted and (stage != state["stage"] or not state["artifact"]):
                    artifact_label += " (historical/stale)"
                text += f"| {stage} | {stage_status} | {artifact_label} | {'none' if stage in accepted else next_action if stage == state['stage'] else 'prior stage approval'} |\n"
            # Immutable materialisations; existing human working files are never overwritten.
            snapshots = [r["state"] for r in state["stage_records"]] + [state]
            for snapshot in snapshots:
                artifact = snapshot["artifact"]
                if not artifact:
                    continue
                rel = ARTIFACTS[snapshot["stage"]]
                folder = self.folder / Path(rel).parent
                folder.mkdir(parents=True, exist_ok=True)
                version = folder / (Path(rel).stem + "-" + artifact["hash"] + ".md")
                if not version.exists():
                    atomic(version, artifact["content"] + "\n")
                working = self.folder / rel
                if working.exists() and "Generated from canonical state; exact content hash" not in working.read_text(encoding="utf-8"):
                    raise GateError("Artifact path contains a human document; archive it before rendering")
                atomic(working, f"# {snapshot['stage']} artifact view\n\nGenerated from canonical state; exact content hash `{artifact['hash']}`.\n\n[Versioned content]({version.name}).\n\n" + artifact["content"] + "\n")
                from .artifacts import entries, relative
                for item in entries(artifact['content']):
                    rel = Path(relative(item)); path = self.folder / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    version = path.with_name(path.stem + '-' + digest(item['content']) + '.md')
                    if not version.exists():
                        atomic(version, item['content'] + '\n')
                    if path.exists() and 'Generated from canonical state; exact content hash' not in path.read_text(encoding='utf-8'):
                        raise GateError('Individual artifact path contains a human document')
                    atomic(path, f"# {item['id']} — {item['type']}\n\nGenerated from canonical state; exact content hash `{digest(item['content'])}`.\nParent: {item['parent'] or 'none'}. Source stage hash: `{artifact['hash']}`.\n\n[Versioned content]({version.name}).\n\n" + item['content'] + '\n')
        for q in state["questions"]:
            text += f"- {q['id']}: {q['text']} — {q['answer'] or 'UNANSWERED'}\n"
        if state["artifact"]:
            text += f"\nArtifact SHA256: {state['artifact']['hash']}\n\n{state['artifact']['content']}\n"
        if state["review"]:
            text += f"\nReview: {state['review']['verdict']} ({state['review']['actor']})\n"
            for finding in state["review"]["findings"]:
                text += f"- {finding['id']}: {finding['impact']}; {finding['resolution']}\n"
        elif blocked and state["reviews"]:
            review = state["reviews"][-1]
            text += f"\nHistorical blocking review (not current approval): {review['run_id']}\n"
            for finding in review["findings"]:
                if finding["blocking"] and finding["disposition"] == "open":
                    text += f"- {finding['id']}: {finding['impact']}; {finding['resolution']}\n"
        atomic(self.folder / "project-status.md", text)
        raid = "# RAID\n\nGenerated by ASDLC from [canonical state](state.json).\n\n"
        for r in state["raid"]:
            raid += f"## {r['id']} — {r['kind']} ({r['status']})\n\nOwner: {r['owner']}\nSource: {r['source']}\nImpact: {r['impact']}\nResponse: {r['response']}\nCreated: {r['created']}\nUpdated: {r['updated']}\n\n"
        atomic(self.folder / "raid.md", raid)

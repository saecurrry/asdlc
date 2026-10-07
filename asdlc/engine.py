from datetime import datetime, timezone
from pathlib import Path
import subprocess
import uuid
import json
from copy import deepcopy

from .store import GateError, digest, validate, resources


def now():
    return datetime.now(timezone.utc).isoformat()


def input_hash(s):
    from .pipeline import input_digest
    return input_digest(s)


def initial(project, target, wiki, fixture, brief, pipeline=False, repair_limit=2):
    target = Path(target).resolve()
    check = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if check.returncode:
        raise GateError("Target must be an existing Git repository")
    if not fixture:
        wiki_check = subprocess.run(["git", "-C", str(Path(wiki).resolve()), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if wiki_check.returncode:
            raise GateError("Wiki must be a separate existing Git clone or labelled fixture")
        if Path(wiki_check.stdout.strip()).resolve() == Path(check.stdout.strip()).resolve():
            raise GateError("Wiki must use a separate Git repository from the target")
    s = dict(schema_version=1, revision=0, project=project, config=dict(target=str(target), wiki=str(Path(wiki).resolve()), fixture=fixture),
             stage="discovery", status="not_started", inputs=dict(brief=brief, resources=resources(wiki)), input_hash="0" * 64,
             questions=[], artifact=None, artifacts=[], dispatch=None, results=[], review=None, reviews=[], repairs=0,
             approvals=[], decisions=[], raid=[], traceability=[])
    if pipeline:
        s.update(schema_version=2, stage_records=[], repair_limit=repair_limit, human_changes_pending=False)
        s["inputs"]["upstream"] = []
        s["inputs"]["code_version"] = None
        from .code_version import capture
        s["code_version"] = capture(target)
    s["input_hash"] = input_hash(s)
    return s


class Engine:
    def __init__(self, store):
        self.store = store

    def change(self, revision, action):
        return self.store.update(revision, action)

    @staticmethod
    def question_raid(s, q):
        if q["blocking"]:
            prefix = "question:" + (s["stage"] + ":" + str(len(s["stage_records"])) + ":" if s["schema_version"] == 2 else "")
            s["raid"].append(dict(id=prefix + q["id"], kind="dependency", owner="human-owner", source=q["id"],
                                  impact="Missing business input: " + q["text"], response="Collect explicit human answer", status="open", created=now(), updated=now()))

    @staticmethod
    def invalidate(s, reset_repairs=False):
        if s["schema_version"] == 2 and reset_repairs:
            from .pipeline import invalidate_pipeline
            invalidate_pipeline(s)
            return
        s["input_hash"] = input_hash(s)
        s["artifact"] = None
        s["review"] = None
        s["dispatch"] = None
        if reset_repairs:
            s["repairs"] = 0
        for a in s["approvals"]:
            a["valid"] = False
        s["status"] = "awaiting_input" if any(q["blocking"] and not q["answer"] for q in s["questions"]) else "stale"
        correction = s.get("human_changes_pending", False) or (s["reviews"] and s["reviews"][-1]["verdict"] in ("changes_required", "blocked"))
        if not reset_repairs and correction:
            if s["repairs"] >= s.get("repair_limit", 2) or (s["reviews"] and s["reviews"][-1]["verdict"] == "blocked"):
                s["status"] = "blocked"
            elif s["status"] != "awaiting_input":
                s["status"] = "changes_requested"

    def start(self, revision):
        def action(s):
            if s["status"] not in ("not_started", "stale"):
                raise GateError("Stage cannot start from current status")
            s["status"] = "awaiting_input" if any(q["blocking"] and not q["answer"] for q in s["questions"]) else "running"
        return self.change(revision, action)

    def question(self, revision, record):
        validate("questions", [record])
        if record["answer"] is not None:
            raise GateError("Questions cannot invent human answers; use answer command")
        def action(s):
            if any(q["id"] == record["id"] for q in s["questions"]):
                raise GateError("Duplicate question")
            s["questions"].append(record)
            self.question_raid(s, record)
            self.invalidate(s)
        return self.change(revision, action)

    def answer(self, revision, qid, answer, actor):
        if not answer.strip() or not actor.strip():
            raise GateError("Answer and actor required")
        def action(s):
            q = next((q for q in s["questions"] if q["id"] == qid), None)
            if not q:
                raise GateError("Unknown question")
            if q["answer"] == answer:
                raise GateError("Duplicate answer")
            q["answer"] = answer
            for r in s["raid"]:
                if r["id"] == "question:" + (s["stage"] + ":" + str(len(s["stage_records"])) + ":" if s["schema_version"] == 2 else "") + qid:
                    r["status"], r["updated"] = "closed", now()
            s["decisions"].append(dict(id=str(uuid.uuid4()), text=f"{qid}: {answer}", rationale="Explicit human answer", alternatives=[], affected=[s["stage"]], actor=actor, date=now()))
            self.invalidate(s)
            if s["status"] == "stale":
                s["status"] = "running"
        return self.change(revision, action)

    def inputs(self, revision, brief):
        if not brief.strip():
            raise GateError("Brief required")
        def action(s):
            if s["inputs"]["brief"] == brief:
                raise GateError("Inputs unchanged; cannot restart repair budget")
            if s["schema_version"] == 2:
                from .pipeline import archive_current
                archive_current(s)
            s["inputs"]["brief"] = brief
            self.invalidate(s, reset_repairs=True)
        return self.change(revision, action)

    def record(self, revision, collection, record):
        if collection not in ("raid", "decisions", "traceability"):
            raise GateError("Unsupported record collection")
        if collection != "traceability":
            validate(collection, [record])
        if collection == "raid" and record["id"].startswith(("finding:", "question:")):
            raise GateError("Generated RAID IDs reserved for orchestrator")
        def action(s):
            if collection != "traceability" and any(r["id"] == record["id"] for r in s[collection]):
                raise GateError("Duplicate record ID")
            if record in s[collection]:
                raise GateError("Duplicate record")
            s[collection].append(record)
        return self.change(revision, action)

    def raid_status(self, revision, rid, status):
        if status not in ("open", "closed"):
            raise GateError("Invalid RAID status")
        def action(s):
            record = next((r for r in s["raid"] if r["id"] == rid), None)
            if not record:
                raise GateError("Unknown RAID record")
            record["status"], record["updated"] = status, now()
        return self.change(revision, action)

    def dispatch(self, revision, kind, actor):
        if kind not in ("worker", "review") or not actor.strip():
            raise GateError("Valid kind and actor required")
        def action(s):
            if s["dispatch"]:
                raise GateError("Pending dispatch; submit or cancel first")
            allowed = ("running", "changes_requested") if kind == "worker" else ("in_review",)
            if s["status"] not in allowed:
                raise GateError("Dispatch forbidden by stage gate")
            if any(q["blocking"] and not q["answer"] for q in s["questions"]):
                raise GateError("Missing business input")
            if kind == "review" and actor == s["artifact"]["owner"]:
                raise GateError("Reviewer must be independent of artifact author")
            if kind == "worker" and s["status"] == "changes_requested":
                if s["repairs"] >= s.get("repair_limit", 2):
                    raise GateError("Repair limit exhausted")
                s["repairs"] += 1
            s["dispatch"] = dict(id=str(uuid.uuid4()), revision=revision + 1, input_hash=s["input_hash"], actor=actor, kind=kind,
                                  artifact_hash=s["artifact"]["hash"] if kind == "review" else None)
        return self.change(revision, action)["dispatch"]

    def cancel(self, revision):
        def action(s):
            if not s["dispatch"]:
                raise GateError("No pending dispatch")
            # Failed/cancelled correction consumes a repair, to bound repeated attempts.
            s["dispatch"] = None
            if s["repairs"] >= s.get("repair_limit", 2) and s["status"] == "changes_requested":
                s["status"] = "blocked"
        return self.change(revision, action)

    def submit(self, result):
        result = deepcopy(result)
        validate("stage-result", result)
        transactions = []
        def action(s):
            if any(r["run_id"] == result["run_id"] for r in s["results"]):
                raise GateError("Duplicate result submission")
            d = s["dispatch"]
            if not d or any(result[k] != d[v] for k, v in [("run_id", "id"), ("revision", "revision"), ("input_hash", "input_hash"), ("kind", "kind"), ("actor", "actor"), ("artifact_hash", "artifact_hash")]):
                raise GateError("Result does not match active dispatch")
            if s["input_hash"] != input_hash(s):
                raise GateError("Input digest mismatch")
            if 'delivery' in result and (s['schema_version'] != 2 or s['stage'] not in ('development', 'testing') or result['kind'] != 'worker'):
                raise GateError('File proposals only permitted for delivery workers')
            if 'delivery' in result and result['questions']:
                if result['delivery']['changes']:
                    raise GateError('Questions must pause before any file proposals')
                from .code_version import capture
                result['code_version'] = capture(s['config']['target'])
                s['code_version'] = result['code_version']
            if 'delivery' not in result and s["schema_version"] == 2 and s["stage"] in ("development", "testing", "sprint-review"):
                from .code_version import capture
                current = capture(s["config"]["target"])
                if result.get("code_version") != current:
                    raise GateError("Delivery-stage result requires the actual commit and dirty code digest")
                s["code_version"] = current
            ids = [q["id"] for q in s["questions"]]
            if len(result["questions"]) > 3:
                raise GateError("At most three questions per round")
            for q in result["questions"]:
                if q["id"] in ids or q["answer"] is not None:
                    raise GateError("Duplicate question or worker-invented answer")
                ids.append(q["id"])
            if len({f["id"] for f in result["findings"]}) != len(result["findings"]):
                raise GateError("Duplicate finding IDs")
            if len({r["id"] for r in result["raid"]}) != len(result["raid"]):
                raise GateError("Duplicate RAID IDs")
            if any(r["id"].startswith(("finding:", "question:")) for r in result["raid"]):
                raise GateError("Generated RAID IDs reserved for orchestrator")
            if result["kind"] == "worker":
                if result["verdict"] != "complete" or not result["content"] or result["findings"]:
                    raise GateError("Invalid worker terminal result")
                if s['schema_version'] == 2:
                    from .artifacts import validate_inventory
                    validate_inventory(s, result['content'])
                if 'delivery' in result and not result['questions']:
                    if s['stage'] == 'testing' and result['delivery']['changes']:
                        raise GateError('Testing cannot propose application changes')
                    from .delivery import Transaction, CheckFailure
                    from .code_version import capture
                    try:
                        transaction = Transaction(s, result['delivery']['changes'])
                    except CheckFailure as failure:
                        result['verdict'] = 'blocked'
                        result['code_version'] = capture(s['config']['target'])
                        result['content'] += '\n\n## Failed executed checks\n\n```json\n' + json.dumps(failure.evidence, indent=2) + '\n```\n'
                        s['results'].append(result)
                        s['dispatch'] = None
                        s['status'] = 'changes_requested' if s['repairs'] < s['repair_limit'] else 'blocked'
                        s['raid'].append(dict(id='delivery:' + result['run_id'], kind='issue', owner='development', source=result['run_id'], impact='Executed delivery checks failed or unavailable', response='Inspect retained result; correct approved scope or request explicit intervention', status='open', created=now(), updated=now()))
                        s['decisions'].append(dict(id='execution:' + result['run_id'], text='Actual failed checks: ' + json.dumps(failure.evidence), rationale='No code integrated and no stage accepted', alternatives=[], affected=['development','testing'], actor='orchestrator', date=now()))
                        if s['stage'] == 'testing':
                            from .pipeline import archive_current, clear_current, upstream
                            budget = max([s['repairs']] + [r['state']['repairs'] for r in s['stage_records'] if r['valid'] and r['state']['stage']=='development'])
                            archive_current(s)
                            for record in s['stage_records']:
                                if record['state']['stage'] in ('development','testing','sprint-review'):
                                    record['valid'] = False
                            s['stage'] = 'development'
                            s['inputs']['upstream'] = upstream(s)
                            s['inputs']['code_version'] = capture(s['config']['target'])
                            s['code_version'] = s['inputs']['code_version']
                            clear_current(s)
                            s['repairs'] = budget
                            s['status'] = 'changes_requested' if budget < s['repair_limit'] else 'blocked'
                        return
                    transactions.append(transaction)
                    transaction.apply()
                    result['code_version'] = capture(s['config']['target'])
                    s['code_version'] = result['code_version']
                    result['content'] += '\n\n## Orchestrator-executed checks\n\n```json\n' + json.dumps(dict(code_version=result['code_version'], checks=transaction.evidence, execution='Approved argv executed on copied source; source bytes unchanged'), indent=2) + '\n```\n'
                s["artifact"] = dict(content=result["content"], hash=digest(result["content"]), input_hash=s["input_hash"], owner=result["actor"], run_id=result["run_id"])
                s["artifacts"].append(s["artifact"].copy())
                s["review"] = None
                s["status"] = "in_review"
            else:
                if result["content"] is not None or result["verdict"] == "complete":
                    raise GateError("Invalid reviewer result")
                if result["verdict"] == "pass" and any(f["blocking"] and f["disposition"] == "open" for f in result["findings"]):
                    raise GateError("Pass cannot contain unresolved blocking findings")
                review = dict(run_id=result["run_id"], actor=result["actor"], artifact_hash=result["artifact_hash"], verdict=result["verdict"], findings=result["findings"])
                s["review"] = review
                s["reviews"].append(review.copy())
                if result["verdict"] == "pass":
                    if "human_changes_pending" in s:
                        s["human_changes_pending"] = False
                    s["status"] = "awaiting_approval"
                    for r in s["raid"]:
                        if r["id"].startswith("finding:"):
                            r["status"], r["updated"] = "closed", now()
                elif result["verdict"] == "changes_required":
                    s["status"] = "blocked" if s["repairs"] >= s.get("repair_limit", 2) else "changes_requested"
                elif result["verdict"] == "needs_human_decision":
                    if not any(q["blocking"] for q in result["questions"]):
                        raise GateError("Missing decision verdict requires blocking question")
                    s["status"] = "awaiting_input"
                else:
                    s["status"] = "blocked"
                for f in result["findings"]:
                    if f["blocking"] and f["disposition"] == "open":
                        s["raid"].append(dict(id="finding:" + result["run_id"] + ":" + f["id"], kind="issue", owner=f["owner"], source=f["id"], impact=f["impact"], response=f["resolution"], status="open", created=now(), updated=now()))
            s["results"].append(result)
            for proposal in result["raid"]:
                existing = next((r for r in s["raid"] if r["id"] == proposal["id"]), None)
                applied = dict(proposal, updated=now())
                if existing:
                    applied["created"] = existing["created"]
                    existing.update(applied)
                else:
                    applied["created"] = now()
                    s["raid"].append(applied)
            s["dispatch"] = None
            if result["questions"]:
                s["questions"].extend(result["questions"])
                for q in result["questions"]:
                    self.question_raid(s, q)
                self.invalidate(s)
                if s["status"] == "stale":
                    s["status"] = "running"
        def on_failure(error):
            # A view failure after canonical commit must not undo accepted code.
            committed = False
            try:
                saved = json.loads(self.store.path.read_text(encoding='utf-8'))
                committed = any(r['run_id'] == result['run_id'] for r in saved['results'])
            except (OSError, ValueError):
                pass
            if not committed:
                for transaction in reversed(transactions):
                    transaction.rollback()
                from .store import atomic
                attempts = self.store.folder / 'attempts'
                attempts.mkdir(exist_ok=True)
                atomic(attempts / ('rejected-' + digest(result) + '.json'), json.dumps(dict(result=result, error=str(error), recorded_at=now()), indent=2) + '\n')
        return self.store.update(result['revision'], action, on_failure=on_failure)

    def approve(self, revision, artifact_hash, actor):
        if not actor.strip():
            raise GateError("Human actor required")
        def action(s):
            a, r = s["artifact"], s["review"]
            if s["status"] != "awaiting_approval" or not a or not r or r["verdict"] != "pass" or r["artifact_hash"] != a["hash"] or artifact_hash != a["hash"] or a["input_hash"] != input_hash(s):
                raise GateError("Approval requires independently reviewed current artifact/input version")
            if any(q["blocking"] and not q["answer"] for q in s["questions"]):
                raise GateError("Unanswered question blocks approval")
            s["approvals"].append(dict(id=str(uuid.uuid4()), actor=actor, artifact_hash=artifact_hash, input_hash=s["input_hash"], date=now(), valid=True))
            s["status"] = "approved"
            if s["schema_version"] == 2:
                from .pipeline import handoff
                handoff(s)
        return self.change(revision, action)

    def run_stage(self, adapter, prompts=None, worker="stage-worker", reviewer="stage-challenger"):
        """Drive serial worker/review/corrections, stopping at every human gate."""
        if not worker.strip() or not reviewer.strip() or worker == reviewer:
            raise GateError("Distinct worker and reviewer identities required")
        state = self.store.resume()
        if state["status"] in ("not_started", "stale"):
            state = self.start(state["revision"])
        attempts = 0
        limit = 2 * (state.get("repair_limit", 2) + 1) + 1
        while state["status"] in ("running", "changes_requested", "in_review"):
            if attempts >= limit:
                raise GateError("Run-stage dispatch limit reached; saved state retained for inspection, not approved")
            attempts += 1
            kind = "review" if state["status"] == "in_review" else "worker"
            actor = reviewer if kind == "review" else worker
            dispatch = state["dispatch"]
            if dispatch:
                if dispatch["actor"] != actor or dispatch["kind"] != kind:
                    raise GateError("Pending dispatch belongs to another actor; submit or cancel explicitly")
            else:
                dispatch = self.dispatch(state["revision"], kind, actor)
                state = self.store.load()
            state = self.submit(adapter.stage(dispatch, state, prompts))
        return state

    def next_sprint(self, revision):
        def action(s):
            if s["schema_version"] != 2 or s["stage"] != "sprint-review" or s["status"] != "approved":
                raise GateError("Next sprint requires the current sprint's exact human acceptance")
            from .pipeline import STAGES, clear_current, upstream
            for record in s["stage_records"]:
                if STAGES.index(record["state"]["stage"]) >= STAGES.index("sprint-planning"):
                    record["valid"] = False  # Historical acceptance retained; no authority for new sprint scope.
            s["stage"] = "sprint-planning"
            s["inputs"]["upstream"] = upstream(s)
            s["inputs"]["code_version"] = None
            clear_current(s)
            s["status"] = "running"
        return self.change(revision, action)

    def reject(self, revision, artifact_hash, actor, reason):
        if not actor.strip() or not reason.strip():
            raise GateError("Human actor and rejection reason required")
        def action(s):
            if s["status"] != "awaiting_approval" or not s["artifact"] or artifact_hash != s["artifact"]["hash"]:
                raise GateError("Rejection requires the current approval target")
            s["decisions"].append(dict(id=str(uuid.uuid4()), text=reason,
                rationale="Explicit human rejection of artifact " + artifact_hash,
                alternatives=[], affected=[s["stage"]], actor=actor, date=now()))
            s["human_changes_pending"] = True
            s["status"] = "blocked" if s["repairs"] >= s.get("repair_limit", 2) else "changes_requested"
        return self.change(revision, action)

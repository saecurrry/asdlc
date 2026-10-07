"""Adapters return results only; they have no authoritative state store."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .store import GateError, validate


def envelope(dispatch, *, content=None, verdict="complete", questions=None, findings=None, raid=None, summary="Fixture result", code_version=None):
    result = dict(run_id=dispatch["id"], revision=dispatch["revision"], input_hash=dispatch["input_hash"],
                kind=dispatch["kind"], actor=dispatch["actor"], artifact_hash=dispatch["artifact_hash"],
                content=content, verdict=verdict, questions=questions or [], findings=findings or [], raid=raid or [], summary=summary)
    if code_version is not None:
        result["code_version"] = code_version
    return result


class FakeAdapter:
    """Explicit synthetic adapter, never a claim of real independent review."""
    def worker(self, dispatch, content):
        return envelope(dispatch, content=content)

    def reviewer(self, dispatch, findings=None):
        return envelope(dispatch, verdict="changes_required" if findings else "pass", findings=findings)


class CodexAdapter:
    def __init__(self, executable="codex", timeout=180):
        self.executable = shutil.which(executable)
        if not self.executable:
            raise GateError("Installed Codex executable not found")
        self.timeout = timeout

    def run(self, prompt, schema, cwd):
        # Each invocation is fresh and read-only, using existing harness auth.
        # Result files are outside authoritative project folders.
        with tempfile.TemporaryDirectory(prefix="asdlc-codex-") as tmp:
            output = Path(tmp) / "result.json"
            command = [self.executable, "exec", "--ephemeral", "--sandbox", "read-only",
                       "--output-schema", str(Path(schema).resolve()), "--output-last-message", str(output), "-"]
            try:
                process = subprocess.run(command, input=prompt, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=self.timeout)
            except subprocess.TimeoutExpired as exc:
                raise GateError("Codex timed out; pending dispatch retained for explicit cancellation/retry") from exc
            if process.returncode or not output.exists():
                raise GateError(f"Codex failed ({process.returncode}); no result applied. {process.stderr[-1500:]}")
            result = json.loads(output.read_text(encoding="utf-8"))
            from jsonschema import Draft202012Validator
            Draft202012Validator(json.loads(Path(schema).read_text(encoding="utf-8"))).validate(result)
            return result

    def stage(self, dispatch, state, prompts):
        root = Path(prompts) if prompts is not None else Path(__file__).parent / "prompts"
        role = state["stage"] if dispatch["kind"] == "worker" else "challenger"
        prompt = (root / (role + ".md")).read_text(encoding="utf-8")
        prompt += "\nReturn only structured result. Do not invoke other agents or write files. Assigned dispatch:\n" + json.dumps(dispatch)
        prompt += "\nScoped project inputs and draft/review context:\n" + json.dumps({k: state[k] for k in ["inputs", "questions", "artifact", "review"]})
        prompt += "\nExisting RAID records for stable-ID proposals (orchestrator applies updates, preserves creation date):\n" + json.dumps(state["raid"])
        prompt += '\nRAID result is proposals only, not a copy of the register. Never return IDs starting finding: or question:; these generated records are owned by the orchestrator. Use ordinary stable IDs or an empty array.'
        prompt += "\nRecorded decisions, including actual human rejection/correction instructions:\n" + json.dumps(state["decisions"])
        if dispatch["kind"] == "worker" and state["status"] == "changes_requested":
            prompt += "\nHistorical correction context (stale evidence, never an approval):\n" + json.dumps({
                "prior_artifact": state["artifacts"][-1] if state["artifacts"] else None,
                "blocking_review": state["reviews"][-1] if state["reviews"] else None,
                "repair_round": state["repairs"],
                "prior_execution": state['results'][-1] if state['results'] else None,
            })
        prompt += f"\nCurrent stage: {state['stage']}. Stage rubric:\n" + (root / (state["stage"] + ".md")).read_text(encoding="utf-8")
        if state['schema_version'] == 2:
            prompt += '\nConfigured runtime policy (versioned implementation rule, no invented business consent):\n' + json.dumps(dict(
                id='serial-exact-gates', version=1, status='configured implementation policy', repair_limit=state['repair_limit'],
                repairs_consumed=state['repairs'], stage=state['stage'],
                accounting='Each correction dispatch consumes one repair; failed executions and material findings return to owner while budget remains.',
                exhaustion='The last allowed correction still receives independent review. Pass with no unresolved blockers permits the human gate. Remaining blockers at the cap hold; no further correction or implicit approval.',
                next_gate='Exact current artifact/input human approval or rejection; orchestrator alone records it and hands off.',
                escalation='Hold for explicit human intervention or a recorded source/scope change; never reset a budget to force a pass.'))
        if state["schema_version"] == 2 and state["stage"] in ("development", "testing", "sprint-review"):
            from .code_version import capture
            prompt += "\nResult MUST include code_version exactly matching the actual target code; verify scope/evidence. Current version:\n" + json.dumps(capture(state["config"]["target"]))
        for name in ("standards", "patterns"):
            sources = [r for r in state["inputs"]["resources"] if r["path"].startswith(name + "/")]
            prompt += f"\nWiki {name}: " + ("not configured / no Markdown sources found" if not sources else "version-bound snapshots in inputs.resources")
        if dispatch['kind'] == 'review':
            prompt += '\nFINAL ROLE RULE: the stage worker contract above is assessment context only. You are the independent REVIEWER. Return kind=review, content=null, delivery=null, artifact_hash exactly assigned. Verdict is pass, changes_required, needs_human_decision or blocked; NEVER complete. Echo assigned dispatch identity. Findings must be meaningful; pass with none is valid.'
        else:
            prompt += '\nFINAL WORKER RULE: return kind=worker, verdict=complete, content=your Markdown artifact and findings=[]. Previous review findings are correction context only; do not echo them in result.findings. Put missing business choices in questions with answer=null and blocking=true. Do not use review verdicts. Scope proposals remain subject to orchestrator validation and human gates.'
        if state['schema_version'] == 2 and state['stage'] in ('development', 'testing') and dispatch['kind'] == 'worker':
            from .delivery import contract, files
            import hashlib
            policy = contract(state)
            inventory = files(Path(state['config']['target']).resolve())
            prompt += '\nApproved delivery contract: ' + json.dumps(policy)
            prompt += '\nCurrent file SHA256: ' + json.dumps({n: hashlib.sha256(b).hexdigest() for n, b in inventory.items()})
            prompt += '\nRemain read-only. Return delivery={"changes":[{"path":"approved/exact/path", "before_sha256":"current digest or null for new file", "content":"complete UTF-8 file or null for deletion"}]}. The orchestrator executes approved tests on a source copy and applies checked proposals. Testing returns changes=[]. Never claim unexecuted tests passed.'
        # Structured Codex output requires every property, using null for inapplicable code refs.
        schema = json.loads((Path(__file__).parent / "schemas" / "stage-result.json").read_text(encoding="utf-8"))
        schema["properties"]["code_version"] = {"anyOf": [schema["properties"]["code_version"], {"type": "null"}]}
        schema['properties']['delivery'] = {'anyOf': [schema['properties']['delivery'], {'type': 'null'}]}
        schema["required"] = list(schema["properties"])
        with tempfile.TemporaryDirectory(prefix="asdlc-schema-") as folder:
            schema_path = Path(folder) / "result-schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            result = self.run(prompt, schema_path, state["config"]["target"])
        if result.get("code_version") is None:
            result.pop("code_version", None)
        if result.get('delivery') is None:
            result.pop('delivery', None)
        if state['schema_version'] == 2 and state['stage'] in ('development', 'testing') and dispatch['kind'] == 'worker' and 'delivery' not in result:
            raise GateError('Built-in delivery worker must return a checked delivery proposal')
        validate("stage-result", result)
        return result

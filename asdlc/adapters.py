"""Adapters return results only; they have no authoritative state store."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .store import GateError, validate


def envelope(dispatch, *, content=None, verdict="complete", questions=None, findings=None, raid=None, summary="Fixture result"):
    return dict(run_id=dispatch["id"], revision=dispatch["revision"], input_hash=dispatch["input_hash"],
                kind=dispatch["kind"], actor=dispatch["actor"], artifact_hash=dispatch["artifact_hash"],
                content=content, verdict=verdict, questions=questions or [], findings=findings or [], raid=raid or [], summary=summary)


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
        root = Path(prompts)
        role = "discovery" if dispatch["kind"] == "worker" else "challenger"
        prompt = (root / (role + ".md")).read_text(encoding="utf-8")
        prompt += "\nReturn only structured result. Do not invoke other agents or write files. Assigned dispatch:\n" + json.dumps(dispatch)
        prompt += "\nScoped project inputs and draft/review context:\n" + json.dumps({k: state[k] for k in ["inputs", "questions", "artifact", "review"]})
        prompt += "\nExisting RAID records for stable-ID proposals (orchestrator applies updates, preserves creation date):\n" + json.dumps(state["raid"])
        if dispatch["kind"] == "worker" and state["status"] == "changes_requested":
            prompt += "\nHistorical correction context (stale evidence, never an approval):\n" + json.dumps({
                "prior_artifact": state["artifacts"][-1] if state["artifacts"] else None,
                "blocking_review": state["reviews"][-1] if state["reviews"] else None,
                "repair_round": state["repairs"],
            })
        prompt += "\nDiscovery rubric:\n" + (root / "discovery.md").read_text(encoding="utf-8")
        for name in ("standards", "patterns"):
            sources = [r for r in state["inputs"]["resources"] if r["path"].startswith(name + "/")]
            prompt += f"\nWiki {name}: " + ("not configured / no Markdown sources found" if not sources else "version-bound snapshots in inputs.resources")
        result = self.run(prompt, Path(__file__).parent / "schemas" / "stage-result.json", state["config"]["target"])
        validate("stage-result", result)
        return result

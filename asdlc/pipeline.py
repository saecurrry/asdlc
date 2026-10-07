"""Serial stage handoffs. Human acceptance is never inferred by this module."""
from copy import deepcopy

from .store import GateError, digest

STAGES = ("discovery", "business-requirements", "architecture", "sprint-planning",
          "development", "testing", "sprint-review")
ARTIFACTS = {
    "discovery": "discovery/brief.md",
    "business-requirements": "requirements/brd.md",
    "architecture": "architecture/hld.md",
    "sprint-planning": "backlog/sprint-plan.md",
    "development": "sprints/implementation.md",
    "testing": "sprints/test-evidence.md",
    "sprint-review": "sprints/sprint-report.md",
}


def upstream(state):
    return [{"stage": r["state"]["stage"], "artifact": deepcopy(r["state"]["artifact"]),
             "approval": deepcopy(r["state"]["approvals"][-1])}
            for r in state["stage_records"] if r["valid"]]


def handoff(state):
    """Called within the same locked transaction as exact human approval."""
    snapshot = deepcopy({k: v for k, v in state.items() if k != "stage_records"})
    state["stage_records"].append({"valid": True, "state": snapshot})
    index = STAGES.index(state["stage"])
    if index == len(STAGES) - 1:
        return  # Approved sprint; a new sprint requires an explicit command.
    state["stage"] = STAGES[index + 1]
    state["inputs"]["upstream"] = upstream(state)
    from .code_version import CODE_STAGES, capture
    if state["stage"] in CODE_STAGES:
        state["code_version"] = capture(state["config"]["target"])
        state["inputs"]["code_version"] = state["code_version"].copy()
    clear_current(state)
    state["status"] = "running"


def clear_current(state):
    state.update(questions=[], artifact=None, artifacts=[], dispatch=None, results=[],
                 review=None, reviews=[], repairs=0, approvals=[], human_changes_pending=False)
    from .engine import input_hash
    state["input_hash"] = input_hash(state)


def invalidate_pipeline(state):
    for record in state["stage_records"]:
        record["valid"] = False
    state["stage"] = "discovery"
    state["inputs"]["upstream"] = []
    state["inputs"]["code_version"] = None
    clear_current(state)
    state["status"] = "stale"


def archive_current(state):
    state["stage_records"].append({"valid": False, "state": deepcopy({k: v for k, v in state.items() if k != "stage_records"})})


def check_pipeline(state, integrity):
    records = state.get("stage_records", [])
    expected = []
    for record in records:
        snapshot = record["state"]
        integrity(snapshot)
        if record["valid"]:
            if snapshot["status"] != "approved" or len(expected) >= len(STAGES) or snapshot["stage"] != STAGES[len(expected)]:
                raise GateError("Stage history requires ordered exact human acceptance")
            if snapshot["inputs"]["upstream"] != expected:
                raise GateError("Stage handoff history does not match approved inputs")
            expected.append({"stage": snapshot["stage"], "artifact": snapshot["artifact"],
                             "approval": snapshot["approvals"][-1]})
    if "stage_records" in state:
        if state["status"] == "approved" and (state["stage"] != "sprint-review" or len(expected) != len(STAGES)):
            raise GateError("Only the final accepted sprint may remain in approved status")
        # The final approved stage is in history as well as the active view.
        active_inputs = expected[:-1] if state["stage"] == "sprint-review" and state["status"] == "approved" else expected
        if state["inputs"]["upstream"] != active_inputs:
            raise GateError("Current stage input handoff mismatch")
        if state["stage"] in ("testing", "sprint-review"):
            accepted_code = next((r["state"]["code_version"] for r in reversed(records)
                                  if r["valid"] and r["state"]["stage"] == "development"), None)
            if state["inputs"]["code_version"] != accepted_code or state["code_version"] != accepted_code:
                raise GateError("Testing and sprint review must bind the accepted development code")
        if state["status"] != "approved":
            next_index = len(expected)
            if next_index >= len(STAGES) or state["stage"] != STAGES[next_index]:
                raise GateError("Stage order bypassed an approval gate")


def input_digest(state):
    payload = {"inputs": state["inputs"], "questions": state["questions"]}
    if state["schema_version"] == 2:
        payload["stage"] = state["stage"]
        payload["repair_limit"] = state["repair_limit"]
    return digest(payload)

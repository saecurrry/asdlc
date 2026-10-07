"""Bind delivery gates to actual Git code, including dirty and untracked bytes."""
import hashlib
import subprocess
from pathlib import Path

from .store import GateError, digest

CODE_STAGES = ("development", "testing", "sprint-review")


def capture(target):
    def git(*args):
        return subprocess.run(["git", "-C", str(target), *args], capture_output=True)
    root = git("rev-parse", "--show-toplevel")
    if root.returncode:
        raise GateError("Target Git repository unavailable")
    folder = Path(root.stdout.decode().strip()).resolve()
    head = git("rev-parse", "HEAD")
    commit = head.stdout.decode().strip() if not head.returncode else "unborn"
    diff = git("diff", "--binary", "HEAD") if not head.returncode else git("diff", "--binary")
    staged = git("diff", "--cached", "--binary")
    other = git("ls-files", "--others", "--exclude-standard", "-z")
    if any(result.returncode for result in (diff, staged, other)):
        raise GateError("Cannot verify target code version")
    files = []
    for name in other.stdout.split(b"\0"):
        if not name:
            continue
        relative = name.decode("utf-8")
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise GateError("Untracked code path escapes target repository")
        files.append((relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    return {"commit": commit, "dirty_digest": digest({"diff": hashlib.sha256(diff.stdout).hexdigest(),
            "staged": hashlib.sha256(staged.stdout).hexdigest(), "untracked": files})}


def refresh(state):
    if state["schema_version"] != 2 or state["stage"] not in CODE_STAGES:
        return False
    current = capture(state["config"]["target"])
    if current == state["code_version"]:
        return False
    # A scoped development worker may change code; its submission must bind the result.
    if state["stage"] == "development" and state["dispatch"] and state["dispatch"]["kind"] == "worker":
        return False
    from .pipeline import archive_current, clear_current, upstream
    archive_current(state)
    for record in state["stage_records"]:
        if record["state"]["stage"] in CODE_STAGES:
            record["valid"] = False
    state["stage"] = "development"
    state["inputs"]["upstream"] = upstream(state)
    state["inputs"]["code_version"] = current
    state["code_version"] = current
    clear_current(state)
    state["status"] = "running"
    return True

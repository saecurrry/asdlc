"""Execute the verification command and record exact source content hashes."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
targets = [root / "pyproject.toml", root / "AGENTS.md"]
for folder in ("asdlc", "schemas", "prompts", "tests", "examples", "tools"):
    targets += [p for p in (root / folder).rglob("*") if p.is_file() and p.suffix in (".py", ".json", ".md") and "__pycache__" not in p.parts]
def manifest():
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(targets))}
before = manifest()
command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
process = subprocess.run(command, cwd=root, capture_output=True, text=True)
after = manifest()
assert before == after, "Sources changed during verification; rerun"
folder = root / "planning/evidence"
folder.mkdir(parents=True, exist_ok=True)
(folder / "test-run.json").write_text(json.dumps({"date": datetime.now(timezone.utc).isoformat(), "command": command,
    "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr, "sha256": after}, indent=2), encoding="utf-8")
print(process.stderr)
sys.exit(process.returncode)

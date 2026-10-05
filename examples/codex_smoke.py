"""Explicit real harness smoke; never approves or dispatches project delivery."""
import json
from pathlib import Path
from asdlc.adapters import CodexAdapter


if __name__ == "__main__":
    root = Path.cwd()
    folder = root / ".asdlc-local/smoke"
    folder.mkdir(parents=True, exist_ok=True)
    schema = folder / "schema.json"
    schema.write_text(json.dumps({"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"], "additionalProperties": False}))
    result = CodexAdapter(timeout=180).run("This is a read-only ASDLC harness connectivity smoke. Do not run tools, read files, delegate, or change anything. Return message equal to ASDLC local Codex smoke passed.", schema, root)
    assert result["message"] == "ASDLC local Codex smoke passed."
    (folder / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))

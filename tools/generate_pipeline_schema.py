"""Generate v2 without overwriting the legacy v1 schemas or specialist prompts."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from asdlc.pipeline import STAGES


def generate():
    base = json.loads((ROOT / "asdlc/schemas/project-state.json").read_text(encoding="utf-8"))
    core = deepcopy(base)
    core["properties"]["schema_version"] = {"const": 2}
    core["properties"]["stage"] = {"enum": list(STAGES)}
    core["properties"]["repair_limit"] = {"type": "integer", "minimum": 0, "maximum": 100}
    core["required"].append("repair_limit")
    core["required"].append("human_changes_pending")
    code = {"type": "object", "properties": {"commit": {"type": "string", "minLength": 1},
            "dirty_digest": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
            "required": ["commit", "dirty_digest"], "additionalProperties": False}
    core["properties"]["code_version"] = deepcopy(code)
    core["required"].append("code_version")
    core["properties"]["inputs"]["properties"]["code_version"] = {"anyOf": [deepcopy(code), {"type": "null"}]}
    core["properties"]["inputs"]["required"].append("code_version")
    ref = {"type": "object", "properties": {
        "stage": {"enum": list(STAGES)}, "artifact": deepcopy(base["properties"]["artifacts"]["items"]),
        "approval": deepcopy(base["properties"]["approvals"]["items"])},
        "required": ["stage", "artifact", "approval"], "additionalProperties": False}
    core["properties"]["inputs"]["properties"]["upstream"] = {"type": "array", "items": ref}
    core["properties"]["inputs"]["required"].append("upstream")
    schema = deepcopy(core)
    schema["properties"]["stage_records"] = {"type": "array", "items": {
        "type": "object", "properties": {"valid": {"type": "boolean"}, "state": core},
        "required": ["valid", "state"], "additionalProperties": False}}
    schema["required"].append("stage_records")
    for folder in ("asdlc/schemas", "schemas"):
        (ROOT / folder / "pipeline-state.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()

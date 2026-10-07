"""Regenerate checked-in schemas and prompt contracts; no project state writes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / 'asdlc' / 'schemas' / 'pipeline-state.json').exists():
    raise SystemExit('Historical v1 generator disabled: it would overwrite current reviewed contracts. '
                     'Edit current schemas/prompts explicitly; mirror prompt changes to asdlc/prompts.')
S = {"type": "string", "minLength": 1}
B = {"type": "boolean"}
I = {"type": "integer", "minimum": 0}
def enum(*v): return {"enum": list(v)}
def arr(v): return {"type": "array", "items": v}
def obj(**p): return {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}
hash_t = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
question = obj(id=S, text=S, blocking=B, answer={"type": ["string", "null"]})
finding = obj(id=S, severity=enum("low", "medium", "high", "critical"), blocking=B,
              location=S, evidence=S, criterion=S, impact=S, resolution=S,
              owner=S, disposition=enum("open", "resolved"))
raid = obj(id=S, kind=enum("risk", "assumption", "issue", "dependency"), owner=S,
           source=S, impact=S, response=S, status=enum("open", "closed"), created=S, updated=S)
decision = obj(id=S, text=S, rationale=S, alternatives=arr(S), affected=arr(S), actor=S, date=S)
approval = obj(id=S, actor=S, artifact_hash=hash_t, input_hash=hash_t, date=S, valid=B)
result = obj(run_id=S, revision=I, input_hash=hash_t, kind=enum("worker", "review"), actor=S,
             artifact_hash={"type": ["string", "null"]}, content={"type": ["string", "null"]},
             questions=arr(question), findings=arr(finding), raid=arr(raid),
             verdict=enum("complete", "pass", "changes_required", "needs_human_decision", "blocked"), summary=S)
dispatch = obj(id=S, revision=I, input_hash=hash_t, actor=S, kind=enum("worker", "review"),
               artifact_hash={"type": ["string", "null"]})
artifact = obj(content=S, hash=hash_t, input_hash=hash_t, owner=S, run_id=S)
review = obj(run_id=S, actor=S, artifact_hash=hash_t, verdict=enum("pass", "changes_required", "needs_human_decision", "blocked"), findings=arr(finding))
state = obj(schema_version=enum(1), revision=I, project=S,
            config=obj(target=S, wiki=S, fixture=B), stage=enum("discovery"),
            status=enum("not_started", "running", "awaiting_input", "in_review", "changes_requested", "awaiting_approval", "approved", "blocked", "stale"),
            inputs=obj(brief=S, resources=arr(obj(path=S, content=S, hash=hash_t))), input_hash=hash_t, questions=arr(question),
            artifact={"anyOf": [artifact, {"type": "null"}]}, artifacts=arr(artifact),
            dispatch={"anyOf": [dispatch, {"type": "null"}]}, results=arr(result),
            review={"anyOf": [review, {"type": "null"}]}, reviews=arr(review),
            repairs=I, approvals=arr(approval), decisions=arr(decision), raid=arr(raid),
            traceability=arr(obj(outcome=S, requirement=S, epic=S, story=S, test=S, code_change=S)))
for name, schema in {"project-state": state, "stage-result": result, "review-findings": arr(finding),
                     "questions": arr(question), "decisions": arr(decision), "approvals": arr(approval), "raid": arr(raid)}.items():
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}
    for folder in [ROOT / "schemas", ROOT / "asdlc" / "schemas"]:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (name + ".json")).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

stages = {
"discovery": ("Understand the business problem in short rounds and produce a brief.", "Configured project, explicit source facts and answered questions.", "Business outcome, actors, scope/exclusions, success measures, unknowns and proposed assumptions clearly distinguished."),
"business-requirements": ("Produce a BRD with measurable intent.", "Approved discovery brief, questions/decisions, standards.", "Stable measurable requirements, business rules, scope/exclusions, initiatives/epics; trace all requirements to outcomes."),
"architecture": ("Produce technical HLD and material decisions.", "Approved BRD and discovery; wiki standards/ and patterns/.", "C4 context/container, selective components, critical sequences, services/partners, data ownership, operations, alternatives and consulted standards."),
"sprint-planning": ("Create small verifiable stories and sprint goals.", "Approved BRD/HLD and constraints.", "Acceptance criteria, appropriate Gherkin, dependencies, serial/parallel eligibility and requirement coverage; no unsupported estimates."),
"development": ("Implement the next approved ready story and tests together.", "Approved story/sprint, BRD/HLD, standards/patterns, exact code base.", "Small scoped changes, acceptance evidence, tests alongside implementation, traceability to story and exact commit plus dirty-tree hash."),
"testing": ("Validate the integrated sprint increment.", "Approved sprint acceptance criteria, integrated code digest and development/review evidence.", "Execute integrated checks; record commands/results and exact revisions; separate skipped/planned checks; regression and defects."),
"sprint-review": ("Report sprint delivery and recommend proceed or hold.", "Approved sprint goal, integrated tests, code digest, review findings and decisions.", "Delivered work, evidence, hard parts, blockers, defects, lessons, followups and proceed/conditions/hold; separate human acceptance."),
}
(ROOT / "prompts").mkdir(exist_ok=True)
for name, (purpose, inputs, criteria) in stages.items():
    (ROOT / "prompts" / (name + ".md")).write_text(f"""# {name} worker contract

## Purpose
{purpose}
## Required inputs
{inputs} Use exact artifact versions supplied by orchestrator. Read applicable central standards/patterns; report their absence. Later stages require approved upstream inputs.
## Permitted actions
Read scoped inputs. Return proposals and structured result only; do not edit canonical state, grant approval or dispatch downstream. Discovery/planning workers are read-only. Development requires separately approved workspace/action scope. No push/merge/deploy.
## Outputs
Return JSON conforming to [stage-result](../schemas/stage-result.json). Echo assigned run_id, revision, input_hash and actor. Worker: kind=worker, verdict=complete, content=Markdown artifact, artifact_hash=null. Review fields/findings empty unless explicitly proposed. Include unresolved questions and RAID proposals with stable IDs. Trace sources by relative links and stable requirement IDs; use Mermaid where helpful.
## Quality criteria and challenger rubric
{criteria} No invented agreed facts, missing material choices, contradictions or unverifiable evidence. Reviewer checks this stage against approved inputs and explicit criteria; zero meaningful findings is valid.
## Questions policy
Ask at most three focused questions per round. Distinguish proposed defaults from confirmed requirements. Return unanswered blocking questions; never answer on the user's behalf. Noninteractive workers cannot wait for interactive input.
## Exit conditions
Complete artifact goes to a fresh independent challenger; blocking findings return to this owner for at most two corrections, then escalate. Missing decisions pause for user. Challenger pass permits exact-version human approval only; worker completion never advances a gate. Changed inputs invalidate outputs/evidence/approvals. Later contracts are design-only until implemented.
""", encoding="utf-8")
(ROOT / "prompts" / "challenger.md").write_text("""# Independent challenger

Purpose: independently assess a named stage, never approve it yourself.
Inputs: target artifact/hash, approved source versions, standards/patterns, stage worker's Quality criteria and challenger rubric, prior findings for corrections. Fresh session; do not reuse author context.
Permitted actions: read-only assessment and structured findings. Never write canonical state, change artifact, implement fixes or grant human acceptance.
Outputs: stage-result JSON with kind=review, exact assigned dispatch metadata, current artifact_hash, content=null, questions/RAID proposals and verdict pass/changes_required/needs_human_decision/blocked. Each finding has stable ID, severity, blocking, location, evidence, criterion, practical impact, requested resolution, owning stage and disposition. A pass has no unresolved blocking findings; zero findings allowed.
Stage rubrics: discovery checks outcomes, success measures, scope, unknowns; BRD checks measurable intent/rules/initiative-epic hierarchy; HLD checks C4/sequences, alternatives, standards, data/integrations/operations; planning checks coverage, small verifiable units and dependencies/eligibility; development checks approved scope, tests, code provenance; testing checks integrated increment and executed evidence; sprint-review checks completeness, readiness and human acceptance distinction.
Questions: missing business choices go to user, not guessed defaults. Missing approved inputs => blocked. Meaningful gaps => changes_required; no mandatory finding quota.
Exit: return report; owning agent corrects, fresh review reruns. Two repair rounds maximum, then escalation; never treat exhaustion as pass.
""", encoding="utf-8")
(ROOT / "prompts" / "orchestrator.md").write_text("""# Orchestrator

Purpose: resume durable workflow and select only deterministic permitted actions.
Inputs: validated configuration/state, exact versions, standards/patterns, approved stage sources and pending records.
Actions: the engine alone writes canonical records with lock/revision checks. Dispatch serial owning worker then independent challenger with minimal explicit context. Do not waive gates, invent answers, approve yourself or infer completion from conversation. Do not dispatch live delivery through drafts. Only discovery is implemented initially.
Outputs: canonical state, generated status/RAID, worker dispatches, persisted results/findings/questions/decisions/approvals/traceability.
Quality: verify schemas, dispatch identity, revision, artifact/input hashes, duplicate IDs and allowed transitions. Independent review and human acceptance separate. At most two repair rounds, then blocked. Changes invalidate affected downstream outputs and approvals.
Questions: collect short rounds of genuine business decisions, preserving unconfirmed assumptions. Pause for missing input or approval without inventing acceptance.
Exit: reviewed exact artifact awaits explicit human approval; unsupported downstream stages stop. Resume canonical state after restart and regenerate views. Corrupt state is an error, not a reset.
""", encoding="utf-8")

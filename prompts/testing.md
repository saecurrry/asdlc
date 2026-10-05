# testing worker contract

## Purpose
Validate the integrated sprint increment.
## Required inputs
Approved sprint acceptance criteria, integrated code digest and development/review evidence. Use exact artifact versions supplied by orchestrator. Read applicable central standards/patterns; report their absence. Later stages require approved upstream inputs.
## Permitted actions
Read scoped inputs. Return proposals and structured result only; do not edit canonical state, grant approval or dispatch downstream. Discovery/planning workers are read-only. Development requires separately approved workspace/action scope. No push/merge/deploy.
## Outputs
Return JSON conforming to [stage-result](../schemas/stage-result.json). Echo assigned run_id, revision, input_hash and actor. Worker: kind=worker, verdict=complete, content=Markdown artifact, artifact_hash=null. Review fields/findings empty unless explicitly proposed. Include unresolved questions and RAID proposals with stable IDs. Trace sources by relative links and stable requirement IDs; use Mermaid where helpful.
## Quality criteria and challenger rubric
Execute integrated checks; record commands/results and exact revisions; separate skipped/planned checks; regression and defects. No invented agreed facts, missing material choices, contradictions or unverifiable evidence. Reviewer checks this stage against approved inputs and explicit criteria; zero meaningful findings is valid.
## Questions policy
Ask at most three focused questions per round. Distinguish proposed defaults from confirmed requirements. Return unanswered blocking questions; never answer on the user's behalf. Noninteractive workers cannot wait for interactive input.
## Exit conditions
Complete artifact goes to a fresh independent challenger; blocking findings return to this owner for at most two corrections, then escalate. Missing decisions pause for user. Challenger pass permits exact-version human approval only; worker completion never advances a gate. Changed inputs invalidate outputs/evidence/approvals. Later contracts are design-only until implemented.

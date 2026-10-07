# ASDLC business requirements — updated draft

Source: user-supplied [replacement design context](design-update-2026-10-05.txt), received 5 October 2026. This is supplied intent, not a new human acceptance of derived documents. No ASDLC rediscovery is required.

## Business need, actors and process

Business owner needs a reusable delivery system that preserves understanding, quality checks and decisions across sessions. Today, conversation history and disconnected artifacts cannot reliably establish what is ready, reviewed or accepted. The future process follows seven stages, with persistent handoffs, independent challenge and explicit human decisions where required by an agreed policy.

Actors: human business owner answers material questions and accepts business/delivery artifacts; orchestrator controls authoritative execution; specialist owns its stage output; independent challenger checks evidence; standards owner approves mandatory guidance. Application source belongs in a project Git repository. Documentation, knowledge and persistent state belong in the central wiki, viewed locally in Obsidian.

Outcomes: **O1** consistent delivery from idea to accepted sprint; **O2** resume without conversation memory or accidental approval; **O3** reusable, bounded learning. Success is demonstrated by a representative project traversing all seven stages with source-to-change traceability, separate review/acceptance and a restart at each human pause. These are proposed verification scenarios, not executed results. Performance/service targets remain project-specific questions.

## Scope

Seven stages: discovery, business requirements, HLD, stories/sprints, development, integrated testing, sprint review/approval. Local Codex first; separate central wiki `saecurrry/asdlc-wiki`; Markdown, portable relative links and diagrams. Shared standards/patterns/knowledge, project lessons and continuously maintained status/RAID are in scope. Release/operational acceptance is an optional explicitly added extension. BMAD is a reference, not a required dependency. Parallel eligibility analysis is required; concurrent execution is not required for the first increment.

## Initiatives and epics

| Initiative | Outcome | Epics | Business purpose |
|---|---|---|---|
| I1 durable control | O2 | E1 state/resume; E2 discovery/governance | Retain facts, decisions and gate evidence |
| I2 governed delivery | O1 | E3 requirements/design/planning; E4 delivery/testing; E5 dependency-aware concurrency | Produce coherent accepted increments |
| I3 reusable learning | O3 | E6 lessons/promotion | Reuse supported findings without turning workarounds into policy |

## Requirements and acceptance expectations

| ID | Requirement | Outcome / epic | Verifiable acceptance |
|---|---|---|---|
| R01 | Run locally with application Git repo and separate central multi-project wiki, preserving established folders. | O1/E1 | Two projects have isolated records; ordinary Markdown works outside Obsidian. |
| R02 | Orchestrate all seven stages with independent challenge, persistent handoffs and separate human acceptance under an explicit policy. | O1/E2–E4 | Stage matrix and representative execution demonstrate no self-approval or gate waiver; optional release is not silently added. |
| R03 | Use short discovery question rounds; persist facts, proposals, unknowns and decisions. | O2/E2 | Unanswered material facts are never agreement; deferral includes owner and required resolution stage. |
| R04 | Produce substantive BRD, initiatives and epics. | O1/E3 | Need, outcomes, users/processes, rules, functional/quality requirements, exceptions, dependencies and acceptance all have sourced coverage. |
| R05 | Discuss execution, hosting/cloud services, partners/integrations, data, identity/security, operations and trade-offs before selecting a stack. | O1/E3 | C4 L1/L2, selected L3 and justified sequence inventory cover requirements; ADR alternatives and guidance/deviations are recorded. |
| R06 | Refine traceable small stories and phased sprints with dependency-aware execution eligibility. | O1/E3/E5 | Every ready story includes purpose, scope, criteria, relevant Gherkin, contracts/guidance, prerequisites, tests and shared-resource analysis. |
| R07 | Develop approved sprint work with tests and independent actual-change review. | O1/E4 | Evidence binds exact code version; material business gaps route to owning stage. |
| R08 | Validate integrated increments and report delivered/verified/accepted work separately. | O1/E4 | Executed/planned/skipped/unavailable checks are distinct; report includes carry-over, difficulties, defects, lessons, RAID and proceed/conditions/hold. |
| R09 | Persist stages, runs, artifacts, questions, decisions, findings, approvals, RAID, stories, sprints and next actions without conflicting authorities. | O2/E1 | Restart derives next permitted action and status/RAID from saved records, without relying on chat. |
| R10 | Protect state integrity and reject stale, duplicate or invalid transitions. | O2/E1 | Simulated stale writer/result/approval cannot change current state; interrupted persistence preserves a recoverable version. Specific storage mechanisms are implementation choices. |
| R11 | Bind approvals/reviews/tests to exact inputs/artifacts/code and assess change impact. | O2/E1/E3 | Changed input marks affected dependency closure stale; historical acceptance remains audit history and cannot authorise current delivery. |
| R12 | Orchestrator owns dispatch/gates; independent challenge routes meaningful findings and missing decisions; retry/escalation policy is explicit. | O1/E2 | No required finding count; exhausted retries hold, never pass. Retry count is a proposed policy, not a business requirement. |
| R13 | Use local Codex initially; report actual integration evidence separately from fixtures. | O1/E2 | Supported integration choice and real results are recorded; language/storage/integration mechanism remain reviewable decisions. |
| R14 | Supply exact document contracts, IDs/metadata/columns/source links and worked examples. | O1/E3 | Every required artifact has a contract and populated synthetic example; indexes alone do not satisfy this requirement. |
| R15 | Capture project lessons and review bounded shared promotion. | O3/E6 | Source/evidence, technology versions, applicability/limits, duplication/contradictions and independent review precede promotion; mandatory standards have owner acceptance. |

## Rules, exceptions and dependencies

BR01 unconfirmed business facts/material choices must be labelled and asked; BR02 blocking findings stop their gate; BR03 zero meaningful findings is valid; BR04 reviewer pass and author completion are not human acceptance; BR05 changed source needs impact assessment; BR06 deferred questions have owners and resolution stages; BR07 shared-resource eligibility precedes parallel dispatch. Missing decisions return to the human through the responsible stage. A coding business gap returns to requirements and invalidates dependent work where appropriate.

Dependencies: available local Codex, authorised project Git workspace, central wiki clone, reviewed applicable guidance and human decisions when needed. Missing standards are reported; index entries alone are not mandatory standards. Availability/performance/security/recovery targets for ASDLC beyond evidence integrity need explicit review, not fabricated numerical commitments.

## Implementation facts and proposals

Delivered foundation: Python 3.10+ serial discovery, schema-validated JSON, local lock/revision/atomic writes, read-only Codex exec adapter, two-repair cap and generated views. Its approved report binds its recorded historical version. These facts do not settle the future language, storage engine, integration mechanism or approval policy. Proposed first extension reuses this runtime serially; default two repairs remains bounded implementation behaviour until configurable policy is implemented. Full pipeline, dependency closure, stories/sprints state and parallel delivery are not automated yet.


## Operator asset implementation note — 6 October 2026

Installed ASDLC must resolve its default operator assets independently of the current directory and exclude framework development records from project inputs. The wheel now includes nine prompts and schemas; clean-install fixture evidence checks v2 init and default prompt lookup. This does not satisfy the separate approved-story coding/integrated-test execution requirements.


## Delivery scope refinement (draft)
R07/R08 implementation requires exact human-approved sprint write paths and argv test commands. Generated code and tests must share the tested byte snapshot; no stale proposal, Git-ignored new file, protected metadata or source-mutating test earns a pass. Missing scope pauses rather than inferring authorization. Initiative/epic/story inventories retain stable parent traceability. Trusted local test commands are not an operating-system security boundary.

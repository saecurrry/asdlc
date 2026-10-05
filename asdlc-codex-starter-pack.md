# Agentic SDLC — local Codex starter pack

## Purpose and use

This is an implementation brief and prompt pack, not a running orchestrator. It creates a reusable agentic SDLC (ASDLC) tool through local Codex. Its first demonstration is discovery, challenger review, repairs, explicit human approval and durable resume.

Save this file in a local tool repository as `asdlc-codex-starter-pack.md`. Start Codex in that repository and use Prompt 1 below. Run subsequent prompts when their prerequisites are met. Use fresh reviewer sessions for independence. Persistent files, not conversation memory, carry progress between sessions.

The system being built and the project it manages are distinct: building ASDLC is the first project; future application projects use the finished tool.

## Confirmed requirements

- Initial harness: Codex locally.
- Reusable orchestration runs against an application Git repository.
- Central ordinary GitHub documentation repository; locally cloned and viewed as an Obsidian vault.
- Stages: ideation/discovery; business requirements; technical HLD; stories and sprint breakdown; sprint development; sprint testing; sprint review and approval. Release/operational acceptance is a proposed extension to confirm.
- An independent challenger reviews every stage against defined criteria. Material gaps return to the owning stage; missing business decisions return to the user.
- Ideation uses rounds of short questions. No unconfirmed business fact or material decision becomes agreed intent.
- Business requirements describe outcomes and rules and organise work into initiatives and epics.
- HLD includes C4 context and container diagrams plus selective component views; important sequences; cloud/services/partner decisions; standards and patterns consulted.
- Stories are small and verifiable, with explicit dependencies and serial/parallel eligibility; grouped into sprints. Gherkin is used where it clarifies behaviour.
- Development consults approved intent, standards and patterns. Tests develop alongside code. Each sprint has integrated validation, review, lessons, blockers and a proceed/hold recommendation.
- Project status and RAID are continuously maintained, with traceability and versioned approval evidence.

## Proposed defaults — require confirmation during discovery

- Serial execution for the first milestone; parallel work added after integration controls exist.
- Three repository roles: reusable ASDLC tool, central wiki, target application. This is a proposed topology, not a supplied set of repository URLs.
- Local CLI; language and storage selected after considering the user's environment.
- File-backed, structured authoritative project state for the serial prototype. A local lock, atomic writes, revision checks and recovery protect updates. Markdown status and RAID are generated views. Add a database only if demonstrated concurrency/recovery requirements justify it.
- One orchestrator writes authoritative state. Workers write isolated result artifacts; challengers do not approve transitions themselves.
- Two automatic repair rounds, then escalation. The limit is configurable and does not turn an unresolved finding into a pass.
- Changes remain local unless commits/pushes/PRs are explicitly authorised by the configured user policy. Merge and deployment policies are separate.

## Decisions still needed

Local operating system; wiki and application paths/URLs; implementation language; interactive approval experience; allowed Git operations; project confidentiality; whether strict timeboxed sprints or delivery batches are preferred; and runtime data retention.

## Proposed repository layout

Tool repo:

```text
AGENTS.md
asdlc-codex-starter-pack.md
planning/
  PLANS.md
  build-plan.md
  discovery.md
  brd.md
  architecture.md
  backlog.md
  reviews/
prompts/
  orchestrator.md
  discovery.md
  business-requirements.md
  architecture.md
  sprint-planning.md
  development.md
  testing.md
  sprint-review.md
  challenger.md
schemas/
src/
tests/
examples/
```

Wiki repo (the exact structure is subject to discovery):

```text
standards/
patterns/
projects/<project-id>/
  index.md
  project-status.md
  raid.md
  discovery/
  requirements/
  architecture/
  decisions/
  backlog/
  sprints/
  reviews/
  approvals/
  state/
```

Use ordinary Markdown, relative links and Mermaid diagrams. No essential content depends on Obsidian plugins. Local Obsidian settings stay out of shared project state. Define where humans edit source documents: generated documents must not silently overwrite human changes.

## Implementation roadmap

These are increments to size after story planning, not committed sprint estimates.

| Increment | Result | Evidence required |
|---|---|---|
| 0. Discovery and design | Approved requirements, architecture and dependency-aware backlog | Fresh challenger reports; human decisions; traceability |
| 1. State foundation | Initialise a project, validate state, generate status/RAID, resume | Invalid transitions refused; atomic-write/recovery tests; no duplicate events |
| 2. Discovery vertical slice | Questions → answers → brief → challenge → repair → approval | Unanswered blocking question prevents advancement; reject/repair loop; approval recorded |
| 3. Planning stages | BRD, HLD, story and sprint agents using shared contracts | Source changes invalidate affected outputs; requirements coverage |
| 4. Serial delivery | One story through development, independent review, tests and sprint acceptance | Evidence linked to exact code revision; integrated sprint validation |
| 5. Parallel execution | Dependency-aware workers with isolated workspaces and integration | Shared-state ownership, conflicts and failed dependencies handled |
| 6. Release and hardening | Approved operational workflow and a real pilot | Restart/failure recovery, release rules and documented limitations |

For each increment maintain a live plan and report outcomes, problems and next steps. Do not generate all implementation code from this roadmap in one pass.

## Stage contract

Every stage definition includes: purpose; required inputs and exact revisions; permitted reads/writes/actions; output schema and files; questions it may ask; objective checks; challenger rubric; blocking conditions; approval policy; retry/escalation policy; and downstream invalidation rules.

Stage statuses: `not_started`, `running`, `awaiting_input`, `in_review`, `changes_requested`, `awaiting_approval`, `approved`, `blocked`, `stale`. Define permitted transitions in code. Review pass and human approval are separate events. Story states are separately defined; do not overload stage status as code completion.

Persist: project/schema version, state revision, current stage/sprint, input artifact hashes/revisions, output versions, run IDs, findings, pending questions, decisions, approvals, RAID records and next action. Approval references artifact hashes and relevant repository commits; local uncommitted artifacts need content hashes. Never pretend a draft hash is a committed revision.

Workers return structured results: run ID, input revision, output artifact references, unresolved questions, findings/RAID proposals, evidence, terminal status and summary. Orchestrator validates and applies a result only against its expected state revision. Reject or reconcile stale results.

RAID covers risks, assumptions, issues and dependencies. Every entry has stable ID, owner, source, impact, response, status and dates. An unresolved assumption is explicitly unconfirmed and cannot substitute for an approved fact. Keep decisions separately with rationale and affected artifacts.

## Challenger contract

Use an independent session/context with approved inputs, target artifacts and rubric. A reviewer may return zero findings. Do not require an arbitrary count or stylistic rewrites.

Each finding records ID, severity, blocking flag, location/evidence, violated criterion, practical impact, requested resolution, responsible stage and disposition. Review verdicts: `pass`, `changes_required`, `needs_human_decision`, `blocked`. A verdict cannot silently accept unresolved blocking findings. Repair verifies each finding and reruns relevant objective checks. Human risk acceptance is explicit, attributable and version-specific.

## Acceptance of the first usable version

1. Initialise a project using local repository paths without requiring GitHub network access.
2. Start discovery and record short questions, answers, unknowns and decisions.
3. Produce a brief and independent challenger report.
4. Return blocking findings to discovery and record the repair history.
5. Pause for missing answers or approval; restart and continue from files.
6. Record approval of a specific artifact version and prevent premature advancement.
7. Generate project status and RAID with correct next action.
8. Rerun without duplicate decisions/events or overwritten human edits.
9. Fail clearly if a required independent worker cannot run; do not substitute self-review while claiming independence.
10. Demonstrate all of this in a temporary fixture, with no merges or deployments.

## Prompt 1 — bootstrap and begin discovery

```text
Read asdlc-codex-starter-pack.md and any existing AGENTS.md. We are building the reusable ASDLC tool described in the pack, starting with local Codex.

Inspect this repository without discarding existing work. Treat confirmed requirements as fixed inputs and proposed defaults as proposals. Create or carefully update AGENTS.md to require persistent planning, short discovery rounds, independent challenger review, source traceability, exact-version approvals, status and RAID maintenance. Respect existing instructions and surface conflicts.

Create planning/PLANS.md defining the living plan format, and planning/build-plan.md containing scope, confirmed facts, open decisions, milestones, validation, progress, decision log and recovery notes. Create planning/discovery.md. Until a wiki path is supplied, keep these bootstrap planning files here and record the wiki connection as pending; do not invent a remote.

Do not implement the application yet. Ask no more than three short questions in the first round: my local OS, the local path/URL of the central wiki repository (or whether it still needs creating), and my preferred implementation language (or whether I want a recommendation). Record answers before asking the next round. Continue discovery until the BRD can be produced without inventing material decisions.

No push, merge, deployment, installation or destructive operation is authorised by this prompt. Local documentation edits are authorised. Finish each turn with what changed and the next action.
```

## Prompt 2 — requirements and design

```text
Read AGENTS.md, the starter pack, planning/build-plan.md and discovery answers. Identify unresolved decisions that block requirements; ask at most three focused questions if needed.

Produce planning/brd.md for the ASDLC tool: business outcomes, scope/exclusions, actors, workflows, functional requirements, measurable quality requirements, initiative/epic hierarchy and acceptance examples. Give requirements stable IDs. Include workflow recovery, challenger independence, Git/wiki concurrency, human edits, approval provenance, change invalidation and evidence integrity.

Once the BRD has passed independent review and I have approved its exact version, produce planning/architecture.md with C4 levels 1 and 2, selective level 3 views, critical sequences, state model, Codex integration approach, repository boundaries and decisions with alternatives. Check current official Codex documentation and the installed version before choosing invocation mechanisms. Do not assume unattended invocations can ask interactive questions: return pending questions and let the orchestrator collect answers.

Run an independent challenger after each artifact, using Prompt 3's contract. Resolve material findings or ask me for decisions. If independent subagents are unavailable, prepare the review input bundle and pause so I can run a fresh reviewer session. Never label self-review independent. Update the plan and RAID. Do not implement until the required approvals exist.
```

## Prompt 3 — independent challenger (fresh session)

```text
Act as the independent challenger for the named stage/artifact. Read AGENTS.md, its approved inputs, target version and stage rubric. Judge the actual artifact against the requirements and standards, not the author's confidence or summary.

Find meaningful omissions, contradictions, unverifiable claims, invented decisions, broken traceability and implementation-blocking ambiguities. For architecture also examine state ownership, restart/retry semantics, repository synchronisation, Codex capabilities and evidence/version binding.

Return pass, changes_required, needs_human_decision or blocked. Write a version-specific report under planning/reviews/ (or the configured project review folder) with finding IDs, evidence, criterion, impact, severity, blocking flag, required resolution and owning stage. Zero material findings is valid. Do not edit the reviewed artifact, update authoritative state, approve business decisions or implement fixes. Report missing inputs rather than guessing.
```

## Prompt 4 — backlog and sprint plan

```text
Read the approved BRD and architecture, reviews, decisions, standards and patterns. Produce planning/backlog.md with initiatives → epics → small stories; stable IDs; linked requirements; acceptance criteria; Gherkin where it clarifies business behaviour; dependencies; verification; and definition of ready/done.

Propose increments following the starter roadmap. Detail the foundation and discovery vertical slice first; leave later increments at appropriate outline depth. Identify spikes separately. Mark serial/parallel eligibility with reasons, but start implementation serially. Do not invent reliable time estimates without evidence.

Obtain independent challenger review for coverage, dependency correctness, feasibility and verifiability; repair material findings. Present the proposed first sprint for my approval and record its exact version. Update the living plan, status and RAID. No implementation yet.
```

## Prompt 5 — implement an approved increment

```text
Read AGENTS.md, the approved plan, architecture, relevant standards/patterns, current status/RAID and the approved sprint stories. Implement only the next ready story in the approved increment. Create a resumable story execution plan before coding.

Use current official Codex documentation and installed CLI help for the harness adapter. Implement deterministic stage transitions and state validation in ordinary code; do not make language-model judgement responsible for enforcing gates. Keep prompts in versioned files and validate structured worker results. Build a fake adapter for deterministic workflow tests and a local Codex adapter for a real smoke demonstration. A fake adapter does not establish real harness integration.

Write meaningful tests for gates, recovery, stale approvals/results, duplicate submissions and failures appropriate to this story. Run relevant checks. Get independent code review using approved intent plus the diff; fix material findings. Missing business/architecture decisions return to their owning stage.

Update the story evidence and living plan. Continue other ready stories within the approved increment only when gates allow it. Respect the configured Git policy; do not push, merge or deploy unless authorised. At the increment boundary stop for sprint review, not a silent transition to the next increment.
```

## Prompt 6 — sprint validation and review

```text
Read the approved sprint goal, stories, code revision, review findings and test evidence. Validate the integrated increment against its acceptance criteria, including real local Codex integration when the adapter is in scope. Record executed checks separately from proposed or skipped checks; record failures and missing evidence honestly.

Create a sprint report with planned/delivered/accepted work, exact code and documentation versions, test evidence, hard parts, blockers, defects, risks, review repairs, lessons and follow-up actions. Obtain independent challenge of the evidence and readiness. Recommend proceed, proceed_with_conditions or hold and explain the conditions.

Update status and RAID through the authorised state owner. Request my sprint acceptance and approval of the next proposed scope. Do not mark the sprint accepted on my behalf or treat a reviewer pass as human approval.
```

## Prompt 7 — resume after a new session

```text
Read AGENTS.md, planning/build-plan.md and the configured project's authoritative state, latest status, RAID, decisions and review/approval records. Reconcile actual files and code revisions with recorded progress. Do not infer completion from conversation history or checkboxes alone.

Report the current stage, last verified result, blocking questions/findings and next permitted action. Resume that action within the approved scope. If inputs changed, mark affected outputs stale and run impact analysis before continuing. Preserve completed history and never repeat external actions merely because a session restarted.
```

## Runtime orchestrator prompt to generate during implementation

The reusable orchestrator prompt must tell Codex to read project configuration and authoritative state, select only permitted actions, load minimum relevant context, dispatch the owning stage, dispatch an independent challenger, apply validated results, update status/RAID, and pause for required input/approval. It cannot waive gates, invent answers, or advance by its own narrative judgement. The engine enforces these rules as well as the prompt describing them.

Every stage prompt should contain purpose, inputs, allowed actions, output contract, questions policy, standards/patterns selection and exit criteria. Avoid one giant prompt containing every project artifact.

## References

- Official OpenAI AGENTS.md guidance: https://developers.openai.com/codex/guides/agents-md
- Official OpenAI persistent execution plans: https://developers.openai.com/cookbook/articles/codex_exec_plans
- Official OpenAI non-interactive Codex: https://developers.openai.com/codex/noninteractive
- BMAD enterprise planning: https://docs.bmad-method.org/plan/plan-inside-an-organization/
- BMAD autonomous build boundary: https://docs.bmad-method.org/build/autonomous-development-loops/

Pin and record framework/tool versions when adopting them; prompts and command names evolve. This pack borrows workflow principles and does not install or assume BMAD.

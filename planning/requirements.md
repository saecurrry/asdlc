# ASDLC requirements — DRAFT, human approval pending

Source: supplied user brief, 5 October 2026. This supersedes unresolved defaults in [starter pack](../asdlc-codex-starter-pack.md). No rediscovery of ASDLC intent is required.

Outcome O1: reusable local delivery with reviewable intent and durable control.
Outcome O2: recover progress without conversation history or accidental acceptance.

| ID | Requirement and measurable acceptance | Epic |
|---|---|---|
| R01 | Run locally against an existing Git target; configure a separate ordinary Git wiki clone with multiple project folders; fixture explicitly labelled when absent. | E1 |
| R02 | Seven stages: discovery, BRD, HLD, planning, development, integrated testing, sprint review/approval. Each has independent challenge and human gates. | E2–E4 |
| R03 | Short discovery rounds preserve questions, answers and unknowns; unanswered blocking questions prevent approval. | E2 |
| R04 | BRD includes measurable requirements, rules, scope/exclusions, initiatives and epics with stable IDs. | E3 |
| R05 | HLD provides C4 context/container, useful components/sequences, service/partner/data/operational choices; consult standards/patterns and record alternatives. | E3 |
| R06 | Small stories include acceptance, dependencies, serial/parallel eligibility and appropriate Gherkin; sprints have goals. | E3 |
| R07 | Development uses approved inputs and tests alongside code; integrated sprint evidence binds exact code versions. | E4 |
| R08 | Sprint reports cover delivery, evidence, hard parts, blockers, defects, lessons and proceed recommendation. Agent review cannot grant human acceptance. | E4 |
| R09 | Canonical status, RAID, decisions, questions, findings, approvals and outcome→requirement→epic→story→test→change links survive restart. | E1 |
| R10 | Schema validation, atomic writes, OS lock and optimistic revisions protect state. Duplicate results and stale approvals are rejected. | E1 |
| R11 | Version-bind inputs, artifacts, reviews, tests and approvals; changed inputs invalidate affected downstream outputs and approvals. | E1/E3 |
| R12 | Orchestrator owns transitions; structured workers cannot mutate state; independent challenger returns findings. Two repairs maximum, then hold. | E2 |
| R13 | Installed local Codex integration uses supported interfaces and existing auth. Fake tests and real integration evidence are reported separately. | E2 |

Business rules: no invented agreement, unresolved material findings block, zero findings is valid, no automatic human acceptance, no live delivery through unapproved stages. Exclusions for first milestone: parallel execution, cloud deployment, automatic Git publication, full planning/delivery agents, remote wiki synchronisation. Later stages are contracts, not implemented capabilities.

Actors: human business owner, CLI orchestrator, owning stage worker, independent challenger. Standards/patterns reside in the wiki root; absence is reported, not filled with invented policy. Proposed implementation defaults (not business facts): Python; local single-host locks; manual CLI approval with actor attribution; immutable inline artifact snapshots in JSON. Wiki location remains unconfigured and does not block the fixture.

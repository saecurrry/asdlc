# Backlog — DRAFT

Initiative I1 durable control (O2): E1 configuration/state; E2 discovery gates.
Initiative I2 governed delivery (O1): E3 planning; E4 sprint execution; E5 parallel integration.

| Story | Requirements | Acceptance / verification | Dependency | Eligibility |
|---|---|---|---|---|
| S01 configure local Git target/wiki | R01 | Reject non-Git target and unsafe project ID; fixture labelled; two projects isolated. | none | serial bootstrap |
| S02 canonical validated store | R09/R10 | Bad schema rejected; stale revision refused; interrupted replace leaves prior valid state; competing writer locked. | S01 | serial state owner |
| S03 generate views/resume | R09 | New process loads canonical record and regenerates status/RAID without repeating results. | S02 | serial writes |
| S04 discovery questions | R03 | Given blocking question, when unanswered, then brief approval is impossible; answered question persists on restart. | S03 | serial shared input |
| S05 worker/reviewer dispatch | R12/R13 | Revision/dispatch/hash checked; duplicate rejected; same owner/reviewer refused; material finding requests correction. | S04 | serial first |
| S06 bounded repairs/approval | R10–R12 | Two corrections allowed; third failed review escalates; exact-hash human approval required; input edit makes approval stale. | S05 | serial gate |
| S07 fixture and Codex smoke | R01/R13 | Script records missing input, repair, review, pause, resume, stale approval and duplicate rejection; separate real schema smoke evidence. | S06 | serial local tests |

Sprint/increment 1 goal: initialise durable state and resume; S01–S03. Increment 2 goal: discovery vertical slice; S04–S07. Foundational fixture implementation authorised by current brief while planning remains draft. Human project delivery approval remains mandatory.

Increment 3 outline: BRD R04, HLD R05, story/sprint R06 agents; input dependency graph; traceability coverage; standards and pattern selection; material decision records. Refine after first milestone feedback.
Increment 4 outline: serial approved stories R07, code review, co-developed tests, integrated validation, exact commit/dirty tree evidence, sprint report and acceptance R08. Increment 5 outline: isolated workers, dependency-aware eligibility, conflict handling, integration owner and combined verification. Do not assign estimates before evidence.

Ready: reviewed inputs and explicit human gate for live projects; fixture can exercise synthetic approvals. Done: acceptance checks, independent challenge, version-bound evidence and human acceptance distinct. Gherkin examples above describe business gate behaviour rather than duplicating implementation details.

# ASDLC implementation backlog — updated draft

Source: [requirements](requirements.md). Foundation S01–S07 is delivered within the historical approved report; these new items are planned, unimplemented and unaccepted. Serial execution is proposed initially. No estimates are asserted.

| ID / parent | Requirement / purpose | Scope and acceptance | Dependencies | Verification / eligibility |
|---|---|---|---|---|
| S08 / I1/E2 policy | R02/R12 explicit gates and retries | Version policy; configurable cap; escalation actor; exact approval targets/conditions; legacy two-repair behaviour retained until migration | Review policy choices | Non-default budgets, exhaustion and unresolved conditions hold; serial shared gate code |
| S09 / I1/E1 full-stage state | R09/R10 canonical seven-stage model | Stages/runs/artifacts/questions/decisions/findings/approvals/RAID/stories/sprints/actions; strict schema and migration | S08, reviewed state design | Validate representative records and migrate discovery without fabricated approvals; serial store |
| S10 / I2/E3 impact graph | R11 dependency closure | Exact refs; source edit produces impact plan and stale closure, preserve unaffected records/history | S09 | Diamond dependency, changed code/guidance and stale approval scenarios; serial graph owner |
| S11 / I2/E3 BRD dispatch | R04/R14 substantive requirements | BRD/initiative/epic artifacts, traceable review criteria and explicit business approval | S09/S10, accepted discovery | Missing rules go to human; correct and challenge; serial artifact/state |
| S12 / I2/E3 HLD dispatch | R05 execution/architecture | C4/sequence inventory/ADR alternatives/guidance/deviations; business gaps route back | S11 | Coverage and operational failure review; serial shared inputs |
| S13 / I2/E3 planning | R06 stories/sprints | Ready/done, acceptance/examples/dependencies/shared-resource analysis; near-term detail | S12 | Cycles/unready dependencies refused; no parallel dispatch merely from story labels |
| S14 / I2/E4 development | R07 approved workspace change | Scoped coding adapter; diff/provenance, tests, independent exact-code review | S13, approved story/workspace | Out-of-scope writes and source gaps hold; serial application workspace |
| S15 / I2/E4 integrated tests | R08 sprint sufficiency | Appropriate tests, exact integrated revision, executed/skipped/unavailable evidence and defects | S14 | Individual passes cannot substitute for failing integration; serial integration owner |
| S16 / I2/E4 sprint acceptance | R08 report/conditions | Carry-over, difficulties, RAID/lessons and recommendation; exact human decision | S15 | Conditional acceptance only advances actions whose conditions are satisfied |
| S17 / I3/E6 learning | R15 bounded reuse | Project capture, versioned evidence/limits, duplicate/contradiction checks and review/promotion | S16 | Workaround cannot auto-create mandatory standard; serial shared wiki |
| S18 / I2/E5 concurrency | R06/R10 safe later scaling | Worktrees, resource ownership, dependency scheduler, integration/combined checks | S13–S16, explicit policy | Conflicting files/interfaces/data serialize; isolated tasks join via verified integration |

Proposed sprint A: S08–S10 durable stage contract; B: S11–S13 planning vertical slice; C: S14–S16 serial sprint delivery; D: S17 learning, then separately reviewed S18 concurrency. Refine each near-term sprint before acceptance; outlines are not delivery approval.

## Near-term story S08

As business owner, I need explicit gate/retry policy so implementation defaults cannot masquerade as agreement. Initiative I1, epic E2; R02/R12; HLD D4/D5. Include policy version, stage review/acceptance points, retry cap and escalation owner; exclude parallel/cloud/release implementation. Dependency: reviewed policy contract. Acceptance: changing policy invalidates affected authorisations; no unknown policy grants approval; foundation two-repair behaviour remains auditable. Tests: non-default cap, exhaustion, policy version change and conditional decision. Serial because gate/state code is shared. This story is draft and not ready until material policy choices and scope are accepted.

```gherkin
Scenario: Retry exhaustion does not approve a stage
  Given a stage has consumed the correction budget in its applicable policy
  And a blocking finding remains
  When the challenger returns changes required
  Then the stage is held for its recorded escalation owner
  And no approval or downstream delivery is created
```


## Packaging progress — 6 October 2026

Installed runtime/prompts/schemas verified from a separate application directory and Python environment. Synthetic probe only; no executed coding or real full Codex pipeline. Remaining priority: S14 scoped coding and S15 executed integrated tests, separate initiative/epic/story outputs, then an end-to-end separate-product demonstration and legacy migration. New packaging increment independently reviewed separately from exact lifecycle evidence.


## Delivery increment execution (draft)
S14/S15 now have exact-file proposal integration and actual check execution, with bounded correction and integration-defect return to development. S11/S13 generate separate initiatives/epics/stories. Product fixture and independent delivery delta review in progress. Unborn Git targets are supported; binary file edits, git/submodule operations, dependency installation and arbitrary build-generated source transformations are outside this exact UTF-8 increment. Legacy migration remains separate.

# Independent implementation review — DRAFT acceptance pending

Review ID: IMPL-2026-10-05-01. Reviewer: independent `implementation_challenger` subagent. Date: 5 October 2026. Verdict: **changes required**. Human acceptance remains pending. No source fixes were made by this reviewer.

## Scope and exact versions

Reviewed the discovery foundation in asdlc/, both schema copies, schema generator, workflow tests and fixture demo against the supplied brief and draft planning. SHA-256 values below identify complete file bytes including line endings. Subsequent repairs require a new independent delta review; this report remains evidence for the original versions.

| Reviewed file | SHA-256 |
|---|---|
| [asdlc/__init__.py](../../asdlc/__init__.py) | `0ad0a9cdcefe9c7b3f786bdbaa5f56ed1e80724cf8fb4be5bc686984307831c2` |
| [asdlc/__main__.py](../../asdlc/__main__.py) | `cf7390a2508a0fcad4777a4a629fc5212ab655cb45845975995f835676a834e3` |
| [asdlc/adapters.py](../../asdlc/adapters.py) | `265bfc81b27dd843d62527b063de7cc3506df7d2e01b4549b81c19c149f0da15` |
| [asdlc/cli.py](../../asdlc/cli.py) | `6c6dd4c6ca6f827823ecb844c584285323da5b8a0c8f6e9babb2f7cecb5a2ed4` |
| [asdlc/engine.py](../../asdlc/engine.py) | `33501cd5ddd1811890a08fe4ad6233f9ac6d5dc2f7ef357acd8e3e4d4b67c96e` |
| [asdlc/schemas/approvals.json](../../asdlc/schemas/approvals.json) | `0189178663c1112eef78f471aee9201befecb7ca5b869f1c1d0c98ef97200a99` |
| [asdlc/schemas/decisions.json](../../asdlc/schemas/decisions.json) | `a8cc4c19b4d8258c117eeb1f7f40b6cf1dfa0aa8559d440a40de094c14ea5790` |
| [asdlc/schemas/project-state.json](../../asdlc/schemas/project-state.json) | `e5dd9c4a9f54f105c07e85f455c8ceed6aacb327e30e907e161ae5d5c93ceb5e` |
| [asdlc/schemas/questions.json](../../asdlc/schemas/questions.json) | `81fc57f18dbb511a9ea670082055a12b4720419bef0827388a2e5c6ceedb9e2b` |
| [asdlc/schemas/raid.json](../../asdlc/schemas/raid.json) | `2c32add575283dfc6d3bf0a296c18bacca2c8282bae6b01d8834558673ea8811` |
| [asdlc/schemas/review-findings.json](../../asdlc/schemas/review-findings.json) | `72db003171d5bf34d36ff60530067fd04615e69a55cad6acb87b22d2d1e3d8be` |
| [asdlc/schemas/stage-result.json](../../asdlc/schemas/stage-result.json) | `b3b016f97f65fbce8568e7fefde9f2a1bad605b24d7c1859347c74e34a1b1d87` |
| [asdlc/store.py](../../asdlc/store.py) | `a5f5e00c5ac8e566f4f43b83c54b3e45e8c760c3a4503658f650d43d910a2c63` |
| [examples/demo.py](../../examples/demo.py) | `7fe3a7180fa4eee7b402ede0baf8248b7484bed22d57800a5ea8b95d0cc720d2` |
| [planning/architecture.md](../../planning/architecture.md) | `c652f892a888e2c8ea176672bcbd95ce8de99946ae0170b454841fd3ac008120` |
| [planning/backlog.md](../../planning/backlog.md) | `9988701250eb5d46d237f6962f4efcdcffac35e1c6719bd030abcf2f3a80609f` |
| [planning/build-plan.md](../../planning/build-plan.md) | `8a24ba703281c31548105bc3684eb9bb32199f30d225950e4921121b710f2f04` |
| [planning/requirements.md](../../planning/requirements.md) | `458ff57011731ad6fe56467513cdd6c5c89822bd92429080fa8fdf6d57080435` |
| [schemas/approvals.json](../../schemas/approvals.json) | `0189178663c1112eef78f471aee9201befecb7ca5b869f1c1d0c98ef97200a99` |
| [schemas/decisions.json](../../schemas/decisions.json) | `a8cc4c19b4d8258c117eeb1f7f40b6cf1dfa0aa8559d440a40de094c14ea5790` |
| [schemas/project-state.json](../../schemas/project-state.json) | `e5dd9c4a9f54f105c07e85f455c8ceed6aacb327e30e907e161ae5d5c93ceb5e` |
| [schemas/questions.json](../../schemas/questions.json) | `81fc57f18dbb511a9ea670082055a12b4720419bef0827388a2e5c6ceedb9e2b` |
| [schemas/raid.json](../../schemas/raid.json) | `2c32add575283dfc6d3bf0a296c18bacca2c8282bae6b01d8834558673ea8811` |
| [schemas/review-findings.json](../../schemas/review-findings.json) | `72db003171d5bf34d36ff60530067fd04615e69a55cad6acb87b22d2d1e3d8be` |
| [schemas/stage-result.json](../../schemas/stage-result.json) | `b3b016f97f65fbce8568e7fefde9f2a1bad605b24d7c1859347c74e34a1b1d87` |
| [tests/test_workflow.py](../../tests/test_workflow.py) | `9325c07ff4db68048ae7079bf949e1f2c22b62d8da8fc7d4bb73eb6db5967a33` |
| [tools/generate_contracts.py](../../tools/generate_contracts.py) | `02aec6163cdcc6dda6ef745e36b133974e3fe7d9ea401a13efef310e9d37ea01` |

Source brief: supplied attachment `68adf716-5a71-4e4a-938d-e7e2dfdbf4e2/Pasted text.txt`, SHA-256 `fa2135d7c98f626f60641ae210f6b16c1c98843eeb324097afa37be9ae4af3f4`.

## Executed evidence

`.venv/Scripts/python.exe -m unittest discover -s tests -v` passed all 10 tests. Separate probes used disposable projects under `.asdlc-local/` and the public Store/Engine/FakeAdapter APIs. They establish failures beyond the current happy-path and schema-corruption tests. Existing checks successfully cover stale revision/result rejection, distinct current author/reviewer attribution, open-blocking pass rejection, normal two-repair exhaustion, missing-input pause, atomic replace failure, process lock and project isolation.

## Findings

### I1 — Stored content can change without invalidating the reviewed hash

Severity: high. Blocking: yes. Owner: storage/orchestrator. Disposition: open.

Location: `asdlc/store.py` Store.load; `asdlc/engine.py` Engine.approve. Evidence: after a worker brief and independent pass, the probe changed only `state.json` artifact.content to `TAMPERED UNREVIEWED BRIEF`, retaining its old hash. Store.resume accepted it; Engine.approve with the old hash returned `approved`. Schema validation checks the hash format but no load/approval path recomputes the artifact content digest. The retained immutable artifact history was likewise unchecked.

Criterion: deterministic hash integrity, corrupt-state refusal and exact-version human approval (confirmed requirement 12 and architecture canonical snapshot promise). Impact: accidental/manual Markdown-content changes can be approved as if the independent reviewer inspected them. This is an integrity check, not a demand for authenticated storage or protection against an attacker who recomputes every value.

Requested resolution: validate semantic state invariants on load and before save/approval, including canonical input digest, artifact/history content hashes, current artifact/review/dispatch binding and approved-state consistency. Reject inconsistent state without rewriting it. Add meaningful schema-valid corruption regression cases.

### I2 — Questions erase the repair count and blocking review gate

Severity: high. Blocking: yes. Owner: discovery/orchestrator. Disposition: open.

Location: `asdlc/engine.py` Engine.submit final questions branch and Engine.invalidate. Evidence: a `changes_required` review with the same open high-severity blocking finding and one new unanswered nonblocking question finished with `status=running, repairs=0`. Repeating worker/review five times produced `running, repairs=0` after every review. Engine.submit first sets changes_requested, then the questions branch calls invalidate, clears the artifact/review, resets repairs, and promotes stale to running. No human answer or changed original brief was involved.

Criterion: two automatic correction rounds then escalation; exhaustion never passes. Impact: a legitimate reviewer proposing optional questions can silently erase unresolved blocking findings from active context and allow unlimited automatic attempts, bypassing a core deterministic gate.

Requested resolution: preserve correction budget and blocking verdict when questions are proposed. Blocking questions should pause while preserving findings/attempt history; nonblocking questions must not reopen unrestricted initial delivery. Define any reset around explicit materially changed human input, document it and test mixed verdict/question cases through exhaustion and restart.

### I3 — Question insertion can persist agreement with no human answer record

Severity: medium. Blocking: yes. Owner: question/orchestrator API. Disposition: open.

Location: `asdlc/engine.py` Engine.question. Evidence: `Engine.question(0, {id: 'Q', text: 'Business consent?', blocking: true, answer: 'Invented agreement'})` succeeded and persisted the answer with decisions=[] and no answer actor/date. Engine.submit rejects worker-invented answers, but the public engine insertion path does not apply the same restriction. The current CLI happens to insert null; the engine contract remains unenforced.

Criterion: never turn unknowns into agreed facts, validate identities in code, preserve explicit answers independently of chat. Impact: a future question collector or local integration can bypass explicit-answer provenance and satisfy a blocking-input gate merely by constructing a schema-valid record.

Requested resolution: require answer=null for all question insertion, with all real answers routed through the explicit answer operation and its decision provenance. Add a regression proving rejection leaves revision/state unchanged.

## Review limits and recommendations

This review does not authenticate local actor strings; the architecture expressly treats them as trusted local audit metadata. It does not claim a synthetic FakeAdapter review is an actual independent business review. It does not prove installed Codex execution; separate real harness evidence remains required. Later delivery stages, Git synchronisation, distributed writers and parallel execution are deferred by scope.

Operational follow-up: nonfixture CLI configuration currently accepts any directory inside a Git worktree, including the target repository itself, as a wiki. Tighten this before live configuration so the documented separate wiki repository boundary is reliably checked. CodexAdapter.stage receives only inputs/questions/artifact/review and no central wiki path or standards manifest; ensure actual central standards and patterns can be discovered and their reviewed versions recorded when configured workflows use them. These observations do not enlarge the current fixture milestone into live delivery.

Resolution status: the three findings are returned to the owning implementation agent. No reviewer self-approval, human consent or live-delivery authorisation is inferred.

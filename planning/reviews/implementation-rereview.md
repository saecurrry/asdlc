# Independent implementation delta review — DRAFT acceptance pending

Review ID: IMPL-2026-10-05-02. Reviewer: independent `implementation_challenger` subagent. Date: 5 October 2026. Verdict: **changes required** for the exact versions below. Human approval remains pending. Review of fixes to [initial review](implementation-review.md); no implementation was edited by this reviewer.

## Findings and independent reproduction

- **I1 resolved:** the original schema-valid artifact-content mutation now fails both resume and approval with `Artifact content digest mismatch`. Inspection confirms load and save invoke semantic integrity checks, including input digest, immutable snapshot digest and structured result/review provenance.
- **I3 resolved:** direct insertion of a preanswered question now fails with `Questions cannot invent human answers; use answer command`. Canonical bytes and revision remain unchanged.
- **I2 budget bypass resolved:** the original optional-question review loop now produces `(changes_requested, 0)`, `(changes_requested, 1)`, `(blocked, 2)` and refuses another worker. The explicit inputs command is the documented human scope-reset boundary.
- **I2 correction context remains unresolved:** submitting a changes_required review plus a nonblocking question invalidates artifact and review. Historical records remain durable, but CodexAdapter.stage passes only current artifact/review, both null. An independent prompt-capture probe used unique markers in the prior artifact and blocking finding; neither marker appeared in the correction prompt. Severity high; blocking yes; owner adapter/orchestrator. Impact: the correction worker lacks the very findings it is meant to repair; a subsequent fresh reviewer also lacks correction history. Requested resolution: explicitly supply the last relevant artifact and failed review as historical correction context, clearly distinguishing stale sources from current evidence. Add a prompt-capture test and preserve the now-correct budget/approval gates.

## Executed checks and scope

`.venv/Scripts/python.exe -m unittest discover -s tests -v` passed all 14 tests. Original three probes were independently rerun in disposable local fixture stores, plus adapter prompt capture without executing Codex. Canonical record/RAID API and CLI changes were read; their existing record/view regression passes. A real installed Codex invocation is separate evidence and is not claimed here.

Local actor attribution remains trusted metadata as documented; later live delivery and distributed/parallel operation remain deferred. Previous operational observations about separate live wiki configuration and central standards context remain follow-ups within their stated scope. Source brief is unchanged from the first review. This report does not grant human approval.

## Exact reviewed file manifest

SHA-256 of complete bytes including line endings. Any changed target requires independent delta review.

| File | SHA-256 |
|---|---|
| [asdlc/__init__.py](../../asdlc/__init__.py) | `0ad0a9cdcefe9c7b3f786bdbaa5f56ed1e80724cf8fb4be5bc686984307831c2` |
| [asdlc/__main__.py](../../asdlc/__main__.py) | `cf7390a2508a0fcad4777a4a629fc5212ab655cb45845975995f835676a834e3` |
| [asdlc/adapters.py](../../asdlc/adapters.py) | `8f8aace1f3479abfd0f08570ea7df4921d4793710823e51d6e3bfce74b4c0982` |
| [asdlc/cli.py](../../asdlc/cli.py) | `48a4c55cd67e44ae98aa630273e1854849f6aa0cac5895f971c485e0c220e5ce` |
| [asdlc/engine.py](../../asdlc/engine.py) | `d478928962b145dcba130336a2901b6233598328d837eea34cb02e758abc4f5b` |
| [asdlc/schemas/approvals.json](../../asdlc/schemas/approvals.json) | `0189178663c1112eef78f471aee9201befecb7ca5b869f1c1d0c98ef97200a99` |
| [asdlc/schemas/decisions.json](../../asdlc/schemas/decisions.json) | `a8cc4c19b4d8258c117eeb1f7f40b6cf1dfa0aa8559d440a40de094c14ea5790` |
| [asdlc/schemas/project-state.json](../../asdlc/schemas/project-state.json) | `e5dd9c4a9f54f105c07e85f455c8ceed6aacb327e30e907e161ae5d5c93ceb5e` |
| [asdlc/schemas/questions.json](../../asdlc/schemas/questions.json) | `81fc57f18dbb511a9ea670082055a12b4720419bef0827388a2e5c6ceedb9e2b` |
| [asdlc/schemas/raid.json](../../asdlc/schemas/raid.json) | `2c32add575283dfc6d3bf0a296c18bacca2c8282bae6b01d8834558673ea8811` |
| [asdlc/schemas/review-findings.json](../../asdlc/schemas/review-findings.json) | `72db003171d5bf34d36ff60530067fd04615e69a55cad6acb87b22d2d1e3d8be` |
| [asdlc/schemas/stage-result.json](../../asdlc/schemas/stage-result.json) | `b3b016f97f65fbce8568e7fefde9f2a1bad605b24d7c1859347c74e34a1b1d87` |
| [asdlc/store.py](../../asdlc/store.py) | `fd0afe6cba9145619cc5da9d7b18f782515dae43d788cfe5ad46bf6792432f29` |
| [examples/demo.py](../../examples/demo.py) | `5536dca84f7620df8c28b3f0d8b0a3271d9029d31f3a405308b21fa3a899ae6d` |
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
| [tests/test_workflow.py](../../tests/test_workflow.py) | `5a321e2032b92359906b06b0b5f00e30927ff0cc0c8c78ef37da032b60bdb4c7` |
| [tools/generate_contracts.py](../../tools/generate_contracts.py) | `02aec6163cdcc6dda6ef745e36b133974e3fe7d9ea401a13efef310e9d37ea01` |

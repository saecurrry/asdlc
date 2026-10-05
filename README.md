# ASDLC

Reusable local agentic SDLC foundation: Python CLI, durable project records, discovery questions, independent challenge, bounded corrections and explicit version-specific human approval. **Foundation preview; planning documents remain draft and human acceptance is pending.** Later planning and sprint delivery stages have prompt contracts/backlog but no runtime yet.

Start with [build plan](planning/build-plan.md), [requirements](planning/requirements.md), [architecture](planning/architecture.md), [backlog](planning/backlog.md) and [validation report](planning/sprint-report.md). The original [starter pack](asdlc-codex-starter-pack.md) is preserved; the current supplied brief authorises foundational local implementation while draft gates still protect live delivery.

## Local setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m examples.demo my-demo
```

Use a new fixture project ID for another demo; existing project state is deliberately never reset. On other platforms use the corresponding virtual-environment Python path. Installation is local to `.venv`; no separate API service or API key is required. Real Codex commands use the installed CLI and its saved authentication/account limits.

The demo writes `.asdlc-local/wiki/projects/my-demo/`, explicitly labelled **LOCAL FIXTURE**. It exercises missing input, correction, fake reviews, synthetic approval, new-process resume and rejection of duplicate/stale submissions. Synthetic approval is not human acceptance of ASDLC or any live project. The final demo state is intentionally stale after an input change.

## Configured project

Use an existing target Git repository and a **separate** existing local wiki Git clone. ASDLC does not create/push remotes. Multiple projects live under `projects/<id>/`; shared `standards/` and `patterns/` Markdown is snapshotted and input-hashed. Missing folders are reported, not invented. Configure real paths through CLI arguments:

```powershell
.\.venv\Scripts\python.exe -m asdlc --wiki C:\Docs\wiki --project example init --target C:\Code\example --brief 'Confirmed business problem'
.\.venv\Scripts\python.exe -m asdlc --wiki C:\Docs\wiki --project example resume
```

Without `--wiki`, the default is `.asdlc-local/wiki` and is always labelled a fixture. Explicit `--fixture` allows a non-Git local wiki for testing.

## Discovery operations

Every mutation takes the expected canonical `--revision` shown by `resume` (except submit, which carries its dispatch revision). Commands:

- `start --revision N`: start discovery from not_started/stale.
- `question --revision N --id Q1 --text 'Success metric?'`: unanswered blocking question (use `--nonblocking` if optional).
- `answer --revision N --id Q1 --text 'Explicit answer' --actor human-name`: attributable answer and decision.
- `dispatch --revision N --kind worker --actor discovery-author`: produce assigned run metadata. Use `--kind review --actor fresh-reviewer` after worker completion.
- `submit result.json`: schema-validated result bound to the exact pending dispatch. See [result schema](schemas/stage-result.json).
- `codex-run --prompts prompts`: run the pending dispatch with a fresh read-only installed Codex process, then submit its validated result. The worker never writes canonical state.
- `cancel --revision N`: clear a failed dispatch; failed corrections consume the bounded budget.
- `approve --revision N --hash CURRENT_HASH --actor human-name`: explicit CLI human approval after independent pass; never automatic.
- `inputs --revision N --brief 'Changed confirmed scope'`: invalidate affected evidence and start a new explicit scope budget.
- `record --revision N --collection raid|decisions|traceability record.json`: persist validated records; `raid-status --revision N --id I1 --status closed` updates RAID.

Run `python -m asdlc --help` or command `--help` for syntax. Canonical JSON stores artifact/result/review histories, decisions, approvals and records. `project-status.md` and `raid.md` are generated owned views; edit human source documentation separately. Resume regenerates views without repeating results. Changed questions, answers, brief or shared standards/patterns invalidate current review/approval. Corrupt state is refused. Stale revisions require reload; two automatic corrections then hold.

## Real harness checks

```powershell
.\.venv\Scripts\python.exe -m examples.codex_smoke
.\.venv\Scripts\python.exe -m examples.codex_fixture_review another-real-fixture
```

The second command challenges a synthetic brief with an actual fresh Codex process and saves [real fixture review evidence](planning/evidence/real-fixture-review.json). It does not grant human approval. These commands may need the host's normal Codex filesystem permissions to initialise its existing local harness database; sandbox failure applies no worker result. A timeout/failed run retains the pending dispatch for explicit cancellation. No bypass flags, new authentication or API billing path are introduced.

Limits: single-host local filesystem locking, serial discovery only, manual Git sync, trusted human CLI attribution (not identity authentication), Markdown standards/patterns only, no automatic later-stage delivery. Parallel execution, complete downstream dependency graph and code/test version binding are planned increments, not implemented claims.

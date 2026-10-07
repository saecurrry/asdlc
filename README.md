# ASDLC

Local serial SDLC orchestration. New projects use schema v2: specialist output → independent challenge → exact human approval → saved next-stage handoff. The seven stages are discovery, BRD, HLD, sprint planning, development, integrated testing and sprint review. Existing schema v1 discovery projects retain their previous behaviour.

## Run a business project

Use an existing application Git repository and a separate wiki clone. Init refuses an existing populated project folder; it does not overwrite human documents or migrate existing v1 state silently.

Install the wheel with `python -m pip install <wheel-path>` in a dedicated environment. The runtime includes its nine specialist/operator contracts and schemas. Commands can run from your application folder; `--prompts <directory>` overrides the bundled contracts. Framework development records are excluded from the wheel.

```powershell
python -m asdlc --wiki C:\Docs\asdlc-wiki --project my-project init --target C:\Code\my-project --brief "The business problem and known facts"
python -m asdlc --wiki C:\Docs\asdlc-wiki --project my-project run-stage
```

`run-stage` manages the current worker, independent reviewer and bounded corrections. It stops at missing input, escalation or exact-hash human approval. Read the generated project status for revision/hash and the stage gate/artifact table. Only an actual human decision authorises `approve`:

```powershell
python -m asdlc --wiki C:\Docs\asdlc-wiki --project my-project approve --revision N --hash CURRENT_HASH --actor human-owner --run-next
```

Approval saves the accepted stage and hands its exact package to the next stage in one transaction. `--run-next` invokes that next specialist/challenger and stops at its next human gate. Without it, the handoff is persisted and `run-stage` continues later. `reject --revision N --hash CURRENT_HASH --actor human-owner --reason "Changes needed"` records rejection and returns the current owner to correction; exhaustion holds. `resume` restores saved progress; it does not infer acceptance. After final sprint acceptance, `next-sprint --revision N` returns to planning, retaining business/HLD inputs and requiring approval of the new scope.

`--repair-limit` on init is a version-bound implementation policy parameter (default two), not a business requirement. `--discovery-only` creates legacy v1 mode. Git synchronisation remains a separately authorised action.

## Execution boundary

The orchestrator can track all seven externally executed stages and validates delivery results against actual commit/dirty/untracked code digests. Code drift reopens development and invalidates affected delivery/testing/sprint authority. Source/guidance changes conservatively restart the dependency chain while preserving history. Stage artifacts and immutable content versions are materialised in the wiki; generated views cannot overwrite a human document.

The built-in Codex process remains read-only and proposes complete UTF-8 file changes. The orchestrator applies them only under the exact write scope of an approved sprint, after executing its test commands against a separate source copy. Testing reruns those commands without proposing writes. Test failures return to bounded development correction; exhaustion holds. Initiative, epic and story inventories become separate generated wiki files. Legacy migration remains outstanding. [Delivery contracts and project use](docs/project-use.md).

ASDLC's own development records under planning/ and wiki projects/asdlc/ are separate from a business project's operating inputs. [Build plan](planning/build-plan.md).

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

# Using ASDLC for a business project

ASDLC's product is a reusable workflow for delivering a user's application project. Building ASDLC itself is a separate development effort and must not be the default task given to an installed agent.

## Repository roles

| Repository | Role |
|---|---|
| ASDLC framework | Installed runtime, specialist/challenger prompts, schemas and reusable templates |
| User application repository | The business project's application code and tests; the coding agent works here |
| Central wiki | Shared standards/patterns/knowledge and `projects/<business-project-id>/` documents, evidence and execution records |

`projects/asdlc/`, the framework's `planning/`, foundation reports and implementation backlog describe development of the framework. They are not inputs for discovering or delivering a new business project.

## What currently works

The implemented schema v2 orchestrator manages serial handoffs across all seven stages, including independent review, exact human approvals, saved history and resume. Legacy v1 retains discovery-only behaviour. Install ASDLC into a dedicated Python environment using `python -m pip install <path-to-asdlc-wheel>`. The wheel includes the runtime, schemas and nine operator contracts; it excludes the framework's development backlog and wiki projects. Default prompts load from the installed package, so commands can run from the application directory. `--prompts <directory>` explicitly overrides them.

Use an existing application Git repository and a separate wiki Git clone:

```powershell
python -m asdlc --wiki C:\Docs\asdlc-wiki --project my-business-project init --target C:\Code\my-business-project --brief "The business problem and known facts"
python -m asdlc --wiki C:\Docs\asdlc-wiki --project my-business-project resume
```

Use a fresh project ID. Init creates authoritative discovery state and generated views; do not initialise over existing human project records without a reviewed preservation plan. No project is started or approved by reading this example.

All-stage orchestration accepts externally executed stage results. Built-in Codex stays read-only and returns structured file proposals; the orchestrator executes approved checks and integrates exact scoped changes. Separate initiative/epic/story files are generated from stage inventories. Legacy migration remains outstanding. Fixture evidence is distinct from real Codex execution and live project acceptance.

## Approved delivery contract

Sprint planning must include one JSON block before its human gate:

````markdown
```asdlc-delivery
{"write_paths":["calculator.py","test_calculator.py"],"test_commands":[["{python}","-m","unittest","discover","-v"]]}
```
````

Paths are exact portable filenames, with no wildcards, protected metadata, links or Windows aliases. Each proposed edit includes its current file SHA-256, or null for a new file. New ignored files cannot be delivered. The orchestrator refuses code drift, failed/unavailable commands and checks that modify source or create unapproved files. Python/pytest caches are allowed disposable outputs. The current increment supports UTF-8 source changes; binary edits, submodules, dependency installation and source-generating builds require a later reviewed contract.

Test commands are argv arrays, executed locally on a separate copied source tree. `{python}` selects ASDLC's interpreter. Commands are trusted project code authorised by sprint approval; copying source is not an OS security boundary. Dependencies must already be available to those commands. Results retain actual commands, exit codes and bounded output. A passing test command is evidence for independent review, not proof that acceptance coverage is sufficient.

BRD and planning output may include one `asdlc-artifacts` JSON array with `id`, `type`, `parent` and complete Markdown `content` for each initiative/epic/story. Epics reference initiatives; stories reference approved epics. Their generated views live under `requirements/initiatives/`, `requirements/epics/` and `backlog/stories/`, with immutable content versions. The enclosing stage gate approves the exact inventory; individual views do not independently grant approval.

## Required project-ready distribution

The deliverable must install reusable ASDLC assets and start a new business project without asking its agent to continue building ASDLC.

1. Setup binds the user's application Git path, central wiki path and new business project ID. It preserves existing content and validates paths before writes.
2. Its agent entry point is a product operating procedure: load that business project's records and applicable shared guidance, then select its next permitted stage/action. It must not load ASDLC's development backlog as the business project's work.
3. The new project receives the established stage folders, exact artifact contracts, independent reviewer criteria and persistent records. No foundation approvals, synthetic decisions or ASDLC-specific initiatives/epics are copied into it.
4. All seven stages must be executable: discovery, substantive BRD with project initiatives/epics, HLD, stories/sprints, scoped coding, integrated testing and sprint review/acceptance. Prompts alone do not meet this criterion.
5. Stage artifacts are materialised in the project's wiki folders and bind source/code versions. Canonical records control transitions; status and RAID display live activity, actual human requests and outstanding work.
6. Questions, correction budgets, independent review, actual human decisions, change impact and resume work across the whole pipeline. Coding gaps route to the responsible earlier stage.
7. Validate the distribution from a clean install against a separate sample business application and wiki. Demonstrate the full artifact trail, coding/testing loop, human pause and process restart. Report fixtures separately from real Codex execution.

## Product readiness

Current status: **serial orchestration, installed operator assets, scoped file delivery, executed checks and individual artifact views implemented and independently reviewed**. A wheel was installed into a separate Python environment, then v2 init and default prompt lookup were exercised from a separate synthetic application's directory. This packaging probe used a synthetic adapter and did not invoke Codex or deliver application code. Reproduce it with `python tools/verify_distribution.py <wheel-path>`; it retains explicit evidence under `.asdlc-local/distribution-checks/`.

The acceptance demonstration must use a business project other than ASDLC, with no dependence on framework development records or this chat's history. Packaging must state current capabilities accurately until that demonstration passes.


The separate calculator sample completed seven fixture gates, generated actual application/test files and executed checks. Development/testing/sprint-review used real installed Codex workers and independent reviewers; upstream documents/reviews and all approval actors were synthetic. This is a validated local delivery sample, not live business acceptance. Final v0.2.0 wheel installation was separately checked from an isolated Python environment/application directory. Broader dependency/build contracts and legacy migration remain outside this increment.


Operate one project against a target at a time. The current increment provides atomic replacement per file and rollback for raised failures; it has no durable multi-file journal or shared application lock across projects. Abrupt termination can require manual source reconciliation before the built-in worker accepts a new proposal. Stronger crash recovery remains follow-on work.

# Central wiki connection

Confirmed by the user: [saecurrry/asdlc-wiki](https://github.com/saecurrry/asdlc-wiki) is the separate documentation, knowledge and sharing repository.

Local clone: `C:/Coding/asdlc-cloud/.asdlc-local/asdlc-wiki`. Branch: `main`; origin: `https://github.com/saecurrry/asdlc-wiki.git`. This clone is ignored by the tool repository and has its own Git history. Open its root as an existing Obsidian vault. Git publication remains manual and is not authorised by the connection request.

The existing standards/, patterns/, knowledge/ and templates/ are preserved. Project documentation lives under projects/asdlc/. The draft tool baseline is copied under projects/asdlc/baseline/ with a SHA-256 provenance manifest; originals remain in this tool repository. Copies are not new approvals and template state is not executable evidence.

## Runtime compatibility

The current CLI accepts this clone through `--wiki .asdlc-local/asdlc-wiki`. It recognises the wiki as a separate Git repository and snapshots shared standards/patterns. The configured target remains this ASDLC tool repository; the project documentation ID is asdlc.

Template alignment completed locally: the wiki now uses the runtime's single project-root state.json and exact version 1 schemas. state/ documents the contract; the older split JSON drafts are preserved as inert legacy templates. The runtime owns generated project-status.md/raid.md after authorised init; archive editable draft views before replacement. No discovery or delivery stage is started by updating templates; supplied ASDLC requirements remain established.

Resume/check invocation after explicit project activation:

```powershell
.\.venv\Scripts\python.exe -m asdlc --wiki .asdlc-local/asdlc-wiki --project asdlc resume
```

Current verification is configuration-only: initial state construction/schema validation against the actual clone, fixture=false, no state persisted and no approval fabricated. Historical tests and review evidence remain bound to their original versions. This connection document is a new configuration record, not a claim those older reviewers reviewed the wiki integration.

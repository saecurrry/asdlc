import argparse
import json
from pathlib import Path
from jsonschema.exceptions import ValidationError

from .engine import Engine, initial
from .store import Store


def main():
    p = argparse.ArgumentParser(description="Local serial ASDLC discovery foundation")
    p.add_argument("--wiki", default=".asdlc-local/wiki", help="Local wiki clone; default is labelled fixture")
    p.add_argument("--project", default="fixture")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--target", required=True)
    init.add_argument("--brief", required=True)
    init.add_argument("--fixture", action="store_true", help="Explicitly label a non-Git wiki as fixture")
    sub.add_parser("resume")
    for command in ["start", "question", "answer", "inputs", "dispatch", "cancel", "approve"]:
        cmd = sub.add_parser(command)
        cmd.add_argument("--revision", type=int, required=True)
        if command == "question":
            cmd.add_argument("--id", required=True)
            cmd.add_argument("--text", required=True)
            cmd.add_argument("--nonblocking", action="store_true")
        if command == "answer":
            cmd.add_argument("--id", required=True)
            cmd.add_argument("--text", required=True)
            cmd.add_argument("--actor", required=True)
        if command == "inputs":
            cmd.add_argument("--brief", required=True)
        if command == "dispatch":
            cmd.add_argument("--kind", choices=["worker", "review"], required=True)
            cmd.add_argument("--actor", required=True)
        if command == "approve":
            cmd.add_argument("--hash", required=True)
            cmd.add_argument("--actor", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("file")
    record = sub.add_parser("record", help="Persist a canonical decision, RAID or traceability proposal")
    record.add_argument("--revision", type=int, required=True)
    record.add_argument("--collection", choices=["decisions", "raid", "traceability"], required=True)
    record.add_argument("file")
    raid = sub.add_parser("raid-status")
    raid.add_argument("--revision", type=int, required=True)
    raid.add_argument("--id", required=True)
    raid.add_argument("--status", choices=["open", "closed"], required=True)
    run = sub.add_parser("codex-run", help="Execute pending dispatch; human approvals stay manual")
    run.add_argument("--prompts", default="prompts")
    args = p.parse_args()
    store = Store(args.wiki, args.project)
    engine = Engine(store)
    try:
        if args.command == "init":
            fixture = args.fixture or args.wiki == ".asdlc-local/wiki"
            if not fixture:
                import subprocess
                probe = subprocess.run(["git", "-C", args.wiki, "rev-parse", "--show-toplevel"], capture_output=True)
                if probe.returncode:
                    p.error("Wiki must be an existing Git clone or explicitly --fixture")
            store.create(initial(args.project, args.target, args.wiki, fixture, args.brief))
            result = store.load()
        elif args.command == "resume":
            result = store.resume()
        elif args.command == "start":
            result = engine.start(args.revision)
        elif args.command == "question":
            result = engine.question(args.revision, dict(id=args.id, text=args.text, blocking=not args.nonblocking, answer=None))
        elif args.command == "answer":
            result = engine.answer(args.revision, args.id, args.text, args.actor)
        elif args.command == "inputs":
            result = engine.inputs(args.revision, args.brief)
        elif args.command == "dispatch":
            result = engine.dispatch(args.revision, args.kind, args.actor)
        elif args.command == "cancel":
            result = engine.cancel(args.revision)
        elif args.command == "approve":
            result = engine.approve(args.revision, args.hash, args.actor)
        elif args.command == "submit":
            result = engine.submit(json.loads(Path(args.file).read_text(encoding="utf-8")))
        elif args.command == "record":
            result = engine.record(args.revision, args.collection, json.loads(Path(args.file).read_text(encoding="utf-8")))
        elif args.command == "raid-status":
            result = engine.raid_status(args.revision, args.id, args.status)
        else:
            from .adapters import CodexAdapter
            state = store.load()
            if not state["dispatch"]:
                p.error("Dispatch required before codex-run")
            result = engine.submit(CodexAdapter().stage(state["dispatch"], state, args.prompts))
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, ValidationError) as exc:
        p.exit(2, f"ASDLC: {exc}\n")


if __name__ == "__main__":
    main()

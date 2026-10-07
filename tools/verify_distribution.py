"""Verify an installed wheel outside the framework checkout; no Codex/live approvals."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import venv
import zipfile


def main():
    wheel = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[1]
    run = root / '.asdlc-local' / 'distribution-checks' / uuid.uuid4().hex
    run.mkdir(parents=True)
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env['TEMP'] = env['TMP'] = str(run)
    runtime = run / 'runtime'
    venv.EnvBuilder(with_pip=True).create(runtime)
    python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    def call(argv, cwd=run):
        result = subprocess.run(argv, cwd=cwd, env=env, text=True, encoding='utf-8',
                                capture_output=True, timeout=180)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    call([str(python), '-m', 'pip', 'install', str(wheel)])
    app = run / 'application'
    app.mkdir()
    call(['git', 'init', str(app)])
    (app / 'app.py').write_text('print("Synthetic install fixture")\n', encoding='utf-8')
    wiki = run / 'fixture-wiki'
    state = json.loads(call([str(python), '-I', '-m', 'asdlc', '--wiki', str(wiki),
                            '--project', 'install-fixture', 'init', '--target', str(app),
                            '--brief', 'Synthetic packaging check, no human acceptance', '--fixture'], cwd=app))
    assert state['schema_version'] == 2 and state['stage'] == 'discovery'
    probe = run / 'probe.py'
    probe.write_text('''import json
from pathlib import Path
import asdlc
from asdlc.adapters import CodexAdapter, envelope
from asdlc.store import Store
from asdlc.engine import Engine
import sys
store = Store(sys.argv[1], "install-fixture")
engine = Engine(store)
engine.start(0)
dispatch = engine.dispatch(store.load()["revision"], "worker", "synthetic-worker")
adapter = object.__new__(CodexAdapter)
def output(prompt, schema, cwd):
    assert "discovery" in prompt
    result = envelope(dispatch, content="# Synthetic installed prompt probe")
    result["code_version"] = None
    return result
adapter.run = output
result = adapter.stage(dispatch, store.load(), None)
assert result["content"].startswith("# Synthetic")
print(json.dumps({"module": asdlc.__file__, "default_prompt_loaded": True}))
''', encoding='utf-8')
    probe_result = json.loads(call([str(python), '-I', str(probe), str(wiki)], cwd=app))
    assert Path(probe_result['module']).is_relative_to(runtime)
    with zipfile.ZipFile(wheel) as archive:
        members = archive.namelist()
        prompts = [name for name in members if name.startswith('asdlc/prompts/')]
        assert len(prompts) == 9
        assert not any(name.startswith(('planning/', 'tests/', 'projects/')) for name in members)
    evidence = dict(wheel=wheel.name, sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                    installed_outside_framework=True, bundled_prompts=len(prompts),
                    schema_v2_init=True, synthetic_adapter_probe=True,
                    real_codex_execution=False, application_delivery=False,
                    live_project_activation=False)
    (run / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(evidence=evidence, path=str(run / 'evidence.json')), indent=2))


if __name__ == '__main__':
    main()

"""Exact-file proposals and executed checks under a human-approved sprint contract.

Test commands are trusted local project code, not an OS security boundary.
Workers propose bytes; only the orchestrator integrates them.
"""
import hashlib
import json
import re
import subprocess
import sys
import os
import shutil
import uuid
from datetime import datetime, timezone
import tempfile
from pathlib import Path, PurePosixPath

from .store import GateError, replace_file


class CheckFailure(GateError):
    def __init__(self, evidence):
        super().__init__('Executed delivery checks failed; evidence retained')
        self.evidence = evidence


def atomic_bytes(path, data):
    fd, name = tempfile.mkstemp(prefix='.asdlc-change-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        replace_file(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def contract(state):
    planning = next((r for r in state['inputs']['upstream'] if r['stage'] == 'sprint-planning'), None)
    if not planning:
        raise GateError('Approved sprint planning required for delivery')
    blocks = re.findall(r'```asdlc-delivery\s*\n(.*?)\n```', planning['artifact']['content'], re.S)
    if len(blocks) != 1:
        raise GateError('Approved sprint needs one asdlc-delivery JSON contract')
    value = json.loads(blocks[0])
    if set(value) != {'write_paths', 'test_commands'} or not isinstance(value['write_paths'], list) or not isinstance(value['test_commands'], list):
        raise GateError('Invalid delivery contract')
    if not value['write_paths'] or len(value['write_paths']) != len(set(value['write_paths'])):
        raise GateError('Distinct exact write paths required')
    for name in value['write_paths']:
        safe_path(name)
    if not value['test_commands'] or len(value['test_commands']) > 20:
        raise GateError('One to twenty approved test commands required')
    for command in value['test_commands']:
        if not isinstance(command, list) or not command or any(not isinstance(v, str) or not v.strip() for v in command):
            raise GateError('Test commands must be nonempty argv arrays')
    return value


def safe_path(name):
    if not isinstance(name, str) or not name or any(c in name for c in '\\:<>"|?*') or any(ord(c) < 32 for c in name):
        raise GateError('Portable relative file path required')
    p = PurePosixPath(name)
    if p.is_absolute() or any(v in ('..', '.', '') or v.lower() in ('.git', '.aws', '.codex', '.asdlc-local') for v in name.split('/')):
        raise GateError('Protected or escaping delivery path')
    for component in name.split('/'):
        stem = component.split('.')[0].upper()
        if component.endswith(('.', ' ')) or stem in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
            raise GateError('Ambiguous Windows file path')
    return p


def target_path(root, name):
    safe_path(name)
    path = root / name
    for parent in [path, *path.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink() or (parent.exists() and getattr(parent.stat(), 'st_file_attributes', 0) & 1024):
            raise GateError('Delivery path contains a link or reparse point')
    if not path.resolve().is_relative_to(root):
        raise GateError('Delivery path escapes application')
    safe_path(path.resolve().relative_to(root).as_posix())
    if path.exists() and not path.is_file():
        raise GateError('Delivery target must be a regular file')
    return path


def files(root):
    check = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if check.returncode or Path(check.stdout.strip()).resolve() != root:
        raise GateError('Delivery target must be the application Git root')
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True)
    if result.returncode:
        raise GateError('Cannot inventory application files')
    inventory = {}
    for raw in result.stdout.split(b'\0'):
        if not raw:
            continue
        name = raw.decode('utf-8')
        path = target_path(root, name)
        if path.exists():
            inventory[name] = path.read_bytes()
    return inventory


def execute_checks(inventory, commands):
    evidence = []
    # Copy only versioned/nonignored source; no credentials or Git configuration.
    with tempfile.TemporaryDirectory(prefix='asdlc-tests-') as folder:
        root = Path(folder)
        for name, data in inventory.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for command in commands:
            argv = [sys.executable if v == '{python}' else v for v in command]
            before_manifest = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in inventory}
            execution = dict(execution_id=str(uuid.uuid4()), started_at=datetime.now(timezone.utc).isoformat(),
                             cwd=str(root.resolve()), argv=argv, resolved_executable=shutil.which(argv[0]),
                             source_before=before_manifest)
            try:
                process = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                                         encoding='utf-8', errors='replace', timeout=60)
                item = dict(command=command, exit_code=process.returncode,
                            stdout=process.stdout[-12000:], stderr=process.stderr[-12000:],
                            stdout_truncated=len(process.stdout)>12000, stderr_truncated=len(process.stderr)>12000,
                            stdout_sha256=hashlib.sha256(process.stdout.encode('utf-8')).hexdigest(),
                            stderr_sha256=hashlib.sha256(process.stderr.encode('utf-8')).hexdigest(), **execution)
            except (subprocess.TimeoutExpired, OSError) as exc:
                def output(name):
                    value = getattr(exc, name, None) or ''
                    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value
                stdout, stderr = output('stdout'), output('stderr')
                evidence.append(dict(command=command, exit_code=None, error=type(exc).__name__,
                                     stdout=stdout[-12000:], stderr=stderr[-12000:],
                                     stdout_truncated=len(stdout)>12000, stderr_truncated=len(stderr)>12000,
                                     stdout_sha256=hashlib.sha256(stdout.encode('utf-8')).hexdigest(),
                                     stderr_sha256=hashlib.sha256(stderr.encode('utf-8')).hexdigest(),
                                     source_after={name: hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).is_file() else None for name in inventory}, **execution))
                raise CheckFailure(evidence) from exc
            evidence.append(item)
            item['source_after'] = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() if (root/name).is_file() else None for name in inventory}
            changed = [name for name, data in inventory.items() if not (root/name).is_file() or (root/name).read_bytes() != data]
            added = [p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in inventory
                     and not ('__pycache__' in p.parts and p.suffix == '.pyc') and '.pytest_cache' not in p.parts]
            if changed or added:
                evidence.append(dict(command=command, exit_code=None, stdout='', stderr='Test modified source or created unapproved files: ' + json.dumps(changed + added)))
                raise CheckFailure(evidence)
            if process.returncode:
                raise CheckFailure(evidence)
    return evidence


class Transaction:
    def __init__(self, state, changes):
        self.root = Path(state['config']['target']).resolve()
        from .code_version import capture
        if capture(self.root) != state['code_version']:
            raise GateError('Application changed since delivery dispatch; inspect and redispatch')
        wiki = Path(state['config']['wiki']).resolve()
        if wiki.is_relative_to(self.root) or self.root.is_relative_to(wiki):
            raise GateError('Delivery application and wiki must not contain one another')
        policy = contract(state)
        self.before = files(self.root)
        self.after = dict(self.before)
        self.paths = []
        for change in changes:
            name = change['path']
            if name not in policy['write_paths'] or name in self.paths:
                raise GateError('Unapproved or duplicate file change')
            if name not in self.before:
                ignored = subprocess.run(['git', '-C', str(self.root), 'check-ignore', '--', name], capture_output=True)
                if ignored.returncode == 0:
                    raise GateError('New delivery file is Git ignored and cannot be version-bound')
            target_path(self.root, name)
            old = self.before.get(name)
            expected = hashlib.sha256(old).hexdigest() if old is not None else None
            if change['before_sha256'] != expected:
                raise GateError('Stale file proposal')
            self.paths.append(name)
            if change['content'] is None:
                self.after.pop(name, None)
            else:
                self.after[name] = change['content'].encode('utf-8')
        self.evidence = execute_checks(self.after, policy['test_commands'])
        self.applied = []

    def apply(self):
        if files(self.root) != self.before:
            raise GateError('Application changed during delivery checks')
        for name in self.paths:
            path = target_path(self.root, name)
            current = path.read_bytes() if path.exists() else None
            if current != self.before.get(name):
                raise GateError('Concurrent application edit; proposal retained')
            path.parent.mkdir(parents=True, exist_ok=True)
            if name in self.after:
                atomic_bytes(path, self.after[name])
            elif path.exists():
                path.unlink()
            self.applied.append(name)
        if files(self.root) != self.after:
            raise GateError('Concurrent application edit during integration; no result accepted')

    def rollback(self):
        conflicts = []
        for name in reversed(self.applied):
            path = target_path(self.root, name)
            current = path.read_bytes() if path.exists() else None
            if current != self.after.get(name):
                conflicts.append(name)
                continue
            if name in self.before:
                atomic_bytes(path, self.before[name])
            elif path.exists():
                path.unlink()
        if conflicts:
            raise GateError('Concurrent edit during rollback; preserved files need inspection: ' + ', '.join(conflicts))

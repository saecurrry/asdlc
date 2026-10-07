import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from asdlc.adapters import envelope, CodexAdapter
from asdlc.engine import Engine, initial
from asdlc.pipeline import STAGES, ARTIFACTS
from asdlc.store import Store, GateError


class SerialAdapter:
    """Explicit synthetic stage evidence, never a real Codex/delivery claim."""
    def stage(self, dispatch, state, prompts):
        from asdlc.code_version import capture
        return envelope(dispatch, content="# Synthetic " + state["stage"] if dispatch["kind"] == "worker" else None,
                        verdict="complete" if dispatch["kind"] == "worker" else "pass",
                        code_version=capture(state['config']['target']) if state['stage'] in ('development', 'testing', 'sprint-review') else None)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        base = Path('.asdlc-local/tests'); base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=base)
        self.target = Path(self.tmp.name) / 'application'; self.target.mkdir()
        subprocess.run(['git', 'init', str(self.target)], check=True, capture_output=True)
        (self.target/'app.py').write_text('print("fixture")\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(self.target), 'add', 'app.py'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.target), '-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid', 'commit', '-m', 'Synthetic fixture'], check=True, capture_output=True)
        self.store = Store(self.tmp.name, 'business-project')
        self.store.create(initial('business-project', self.target, self.tmp.name, True,
                                  'Synthetic business project', pipeline=True))
        self.engine = Engine(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def accept(self):
        s = self.store.load()
        return self.engine.approve(s['revision'], s['artifact']['hash'], 'synthetic-human')

    def test_seven_stage_handoffs_pause_at_each_gate_and_resume(self):
        for index, stage in enumerate(STAGES):
            s = Engine(Store(self.tmp.name, 'business-project')).run_stage(SerialAdapter())
            self.assertEqual((s['stage'], s['status']), (stage, 'awaiting_approval'))
            self.assertEqual(len(s['stage_records']), index)
            self.assertEqual(len(s['inputs']['upstream']), index)
            self.assertTrue((self.store.folder / ARTIFACTS[stage]).exists())
            self.assertIn('Waiting on you', (self.store.folder / 'project-status.md').read_text(encoding='utf-8'))
            with self.assertRaises(GateError):
                self.engine.approve(s['revision'], '0'*64, 'synthetic-human')
            s = self.accept()
            self.assertEqual(s['stage'], STAGES[min(index+1, 6)])
            self.assertEqual(s['status'], 'approved' if index == 6 else 'running')
            if index == 2:
                process = subprocess.run([sys.executable, '-m', 'asdlc', '--wiki', self.tmp.name,
                                          '--project', 'business-project', 'resume'], capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stderr)
                resumed = json.loads(process.stdout)
                self.assertEqual((resumed['stage'], len(resumed['stage_records'])), ('sprint-planning', 3))
        self.assertEqual(len(self.store.resume()['stage_records']), 7)

    def test_changed_source_invalidates_handoffs_and_preserves_history(self):
        self.engine.run_stage(SerialAdapter()); self.accept()
        self.engine.run_stage(SerialAdapter())
        old = self.store.load()
        s = self.engine.inputs(old['revision'], 'Changed synthetic outcome')
        self.assertEqual((s['stage'], s['status']), ('discovery', 'stale'))
        self.assertTrue(all(not r['valid'] for r in s['stage_records']))
        self.assertTrue(any(r['state']['stage'] == 'business-requirements' for r in s['stage_records']))
        with self.assertRaises(GateError):
            self.engine.approve(s['revision'], old['artifact']['hash'], 'synthetic-human')
        self.store.resume()

    def test_forged_handoff_and_stage_skip_are_rejected(self):
        self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.store.load(); s['inputs']['upstream'][0]['approval']['actor'] = 'forged'
        from asdlc.engine import input_hash
        s['input_hash'] = input_hash(s)
        with self.assertRaises(GateError): self.store.save(s)

    def test_failure_keeps_dispatch_and_configurable_repairs_hold(self):
        class Failure:
            def stage(self, *args): raise GateError('Synthetic process failure')
        with self.assertRaises(GateError): self.engine.run_stage(Failure())
        s = self.store.resume(); self.assertIsNotNone(s['dispatch'])
        s = self.engine.run_stage(SerialAdapter())
        self.assertEqual(s['status'], 'awaiting_approval')
        self.assertEqual(len(s['results']), 2)

    def test_zero_repair_policy_holds_after_first_material_finding(self):
        other = Store(self.tmp.name, 'zero-repairs')
        other.create(initial('zero-repairs', Path.cwd(), self.tmp.name, True, 'Synthetic', pipeline=True, repair_limit=0))
        engine = Engine(other)
        class Gap:
            def stage(self, d, state, prompts):
                if d['kind'] == 'worker': return envelope(d, content='Synthetic draft')
                finding = dict(id='F1', severity='high', blocking=True, location='artifact', evidence='Synthetic gap', criterion='Complete', impact='Unready', resolution='Resolve gap', owner=state['stage'], disposition='open')
                return envelope(d, verdict='changes_required', findings=[finding])
        s = engine.run_stage(Gap())
        self.assertEqual((s['status'], s['repairs']), ('blocked', 0))
        self.assertEqual(len(s['stage_records']), 0)

    def test_resource_change_resets_pipeline_and_retains_accepted_history(self):
        self.engine.run_stage(SerialAdapter()); self.accept()
        folder = Path(self.tmp.name) / 'standards'; folder.mkdir()
        (folder/'new.md').write_text('New synthetic constraint', encoding='utf-8')
        s = self.store.resume()
        self.assertEqual((s['stage'], s['status']), ('discovery', 'stale'))
        self.assertTrue(any(r['state']['status']=='approved' for r in s['stage_records']))
        self.assertFalse(any(r['valid'] for r in s['stage_records']))

    def test_stage_prompt_and_approved_package_are_dispatched(self):
        self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.store.load(); d = self.engine.dispatch(s['revision'], 'worker', 'brd-worker')
        s = self.store.load(); adapter = CodexAdapter.__new__(CodexAdapter)
        captured = []
        def output(prompt, schema, cwd):
            captured.append(prompt)
            contract = json.loads(Path(schema).read_text(encoding='utf-8'))
            self.assertEqual(set(contract['required']), set(contract['properties']))
            result = envelope(d, content='Synthetic BRD')
            result['code_version'] = None
            return result
        adapter.run = output
        result = adapter.stage(d, s, 'prompts')
        self.assertNotIn('code_version', result)
        self.assertIn('business-requirements', captured[0])
        self.assertIn(s['inputs']['upstream'][0]['artifact']['hash'], captured[0])

    def test_init_refuses_existing_human_documents(self):
        other = Store(self.tmp.name, 'existing')
        other.folder.mkdir(parents=True)
        (other.folder/'project-status.md').write_text('human record')
        with self.assertRaises(GateError):
            other.create(initial('existing', Path.cwd(), self.tmp.name, True, 'Synthetic', pipeline=True))
        self.assertEqual((other.folder/'project-status.md').read_text(), 'human record')

    def test_later_question_id_does_not_reopen_or_close_prior_stage_raid(self):
        self.engine.start(0)
        q = dict(id='Q1', text='Synthetic question?', blocking=True, answer=None)
        s = self.engine.question(self.store.load()['revision'], q)
        self.engine.answer(s['revision'], 'Q1', 'First answer', 'synthetic-human')
        self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.engine.question(self.store.load()['revision'], q)
        rows = [r for r in s['raid'] if r['id'].startswith('question:')]
        self.assertEqual(len({r['id'] for r in rows}), 2)
        self.assertEqual([r['status'] for r in rows], ['closed', 'open'])
        self.engine.answer(s['revision'], 'Q1', 'Second answer', 'synthetic-human')

    def test_materialized_version_tamper_stops_resume(self):
        self.engine.run_stage(SerialAdapter()); s = self.store.load()
        version = next((self.store.folder/'discovery').glob('brief-*.md'))
        version.write_text('Changed bytes', encoding='utf-8')
        with self.assertRaises(GateError): self.store.resume()

    def test_retry_policy_edit_invalidates_bound_digest(self):
        s = self.store.load(); s['repair_limit'] = 99
        with self.assertRaises(GateError): self.store.save(s)

    def test_dirty_code_blocks_stale_test_approval_and_reopens_development(self):
        for _ in range(5):
            self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.engine.run_stage(SerialAdapter())
        self.assertEqual(s['stage'], 'testing')
        (self.target/'app.py').write_text('print("changed")\n', encoding='utf-8')
        with self.assertRaises(GateError): self.engine.approve(s['revision'], s['artifact']['hash'], 'synthetic-human')
        new = self.store.resume()
        self.assertEqual((new['stage'], new['status']), ('development', 'running'))
        self.assertEqual(len([r for r in new['stage_records'] if r['valid']]), 4)

    def test_delivery_result_without_actual_code_version_is_rejected(self):
        for _ in range(4):
            self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.store.load(); d = self.engine.dispatch(s['revision'], 'worker', 'external-developer')
        with self.assertRaises(GateError): self.engine.submit(envelope(d, content='Unsupported delivery claim'))

    def test_next_sprint_preserves_business_inputs_but_requires_new_scope_approval(self):
        with self.assertRaises(GateError): self.engine.next_sprint(self.store.load()['revision'])
        for _ in STAGES:
            self.engine.run_stage(SerialAdapter()); self.accept()
        s = self.engine.next_sprint(self.store.load()['revision'])
        self.assertEqual((s['stage'], s['status']), ('sprint-planning', 'running'))
        self.assertEqual(len(s['inputs']['upstream']), 3)
        self.assertTrue(any(r['state']['stage']=='sprint-review' and r['state']['status']=='approved' for r in s['stage_records']))
        self.assertEqual(self.engine.run_stage(SerialAdapter())['status'], 'awaiting_approval')

    def test_human_rejection_returns_to_owner_without_handoff(self):
        s = self.engine.run_stage(SerialAdapter())
        s = self.engine.reject(s['revision'], s['artifact']['hash'], 'synthetic-human', 'Clarify the scope')
        self.assertEqual((s['stage'], s['status'], len(s['stage_records'])), ('discovery', 'changes_requested', 0))
        self.assertEqual(s['decisions'][-1]['text'], 'Clarify the scope')
        s = self.engine.run_stage(SerialAdapter())
        self.assertEqual(s['status'], 'awaiting_approval')
        self.assertFalse(s['approvals'])

    def test_optional_questions_cannot_erase_human_rejection_repair_budget(self):
        s = self.engine.run_stage(SerialAdapter())
        self.engine.reject(s['revision'], s['artifact']['hash'], 'synthetic-human', 'Clarify scope')
        for n in range(2):
            s = self.store.load(); d = self.engine.dispatch(s['revision'], 'worker', 'owner')
            q = dict(id=f'OPTIONAL-{n}', text='Optional detail?', blocking=False, answer=None)
            self.engine.submit(envelope(d, content='Synthetic correction', questions=[q]))
        s = self.store.load()
        self.assertEqual((s['status'], s['repairs'], s['human_changes_pending']), ('blocked', 2, True))
        with self.assertRaises(GateError): self.engine.dispatch(s['revision'], 'worker', 'owner')


if __name__ == '__main__':
    unittest.main()

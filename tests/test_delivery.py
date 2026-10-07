import hashlib
import json
import sys
import unittest
from unittest.mock import patch

import test_pipeline
from test_pipeline import SerialAdapter
from asdlc.adapters import envelope
from asdlc.store import GateError


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        test_pipeline.PipelineTests.setUp(self)
        from asdlc.engine import Engine, initial
        from asdlc.store import Store
        from pathlib import Path
        self.store = Store(Path(self.tmp.name) / 'separate-wiki', 'business-project')
        self.store.create(initial('business-project', self.target, self.store.wiki, True,
                                  'Synthetic delivery project', pipeline=True))
        self.engine = Engine(self.store)
    tearDown = test_pipeline.PipelineTests.tearDown
    accept = test_pipeline.PipelineTests.accept
    def ready(self, command=None):
        for _ in range(3):
            self.engine.run_stage(SerialAdapter()); self.accept()
        policy = dict(write_paths=['app.py'], test_commands=[command or ['{python}', 'app.py']])
        class Planner:
            def stage(self, d, s, prompts):
                return envelope(d, content='# Synthetic sprint\n```asdlc-delivery\n'+json.dumps(policy)+'\n```' if d['kind']=='worker' else None,
                                verdict='complete' if d['kind']=='worker' else 'pass')
        self.engine.run_stage(Planner()); self.accept()
        s=self.store.load(); return self.engine.dispatch(s['revision'],'worker','synthetic-developer')

    def proposal(self, d, content='print("delivered")\n', path='app.py'):
        r=envelope(d, content='# Synthetic implementation')
        r['delivery']={'changes':[dict(path=path,before_sha256=hashlib.sha256((self.target/'app.py').read_bytes()).hexdigest(),content=content)]}
        return r

    def test_scoped_delivery_applies_and_records_executed_checks(self):
        d=self.ready(); s=self.engine.submit(self.proposal(d))
        self.assertEqual((self.target/'app.py').read_text(),'print("delivered")\n')
        self.assertEqual(s['status'],'in_review')
        self.assertIn('Orchestrator-executed checks',s['artifact']['content'])
        self.assertIn('"exit_code": 0',s['artifact']['content'])
        self.assertIsNotNone(s['results'][-1]['code_version'])

    def test_out_of_scope_stale_and_failed_tests_preserve_application(self):
        d=self.ready(); before=(self.target/'app.py').read_bytes()
        for r in [self.proposal(d,path='../outside.py')]:
            with self.assertRaises(GateError): self.engine.submit(r)
            self.assertEqual((self.target/'app.py').read_bytes(),before)
            self.assertIsNotNone(self.store.load()['dispatch'])
        r=self.proposal(d); r['delivery']['changes'][0]['before_sha256']='0'*64
        with self.assertRaises(GateError): self.engine.submit(r)
        s=self.engine.submit(self.proposal(d,content='raise RuntimeError("failure")\n'))
        self.assertEqual(s['status'],'changes_requested')
        self.assertIn('Failed executed checks',s['results'][-1]['content'])
        self.assertEqual((self.target/'app.py').read_bytes(),before)

    def test_failed_canonical_save_rolls_back_code(self):
        d=self.ready(); before=(self.target/'app.py').read_bytes()
        with patch.object(self.store,'save',side_effect=OSError('Synthetic write failure')):
            with self.assertRaises(OSError): self.engine.submit(self.proposal(d))
        self.assertEqual((self.target/'app.py').read_bytes(),before)

    def test_testing_runs_checks_without_changing_application(self):
        d=self.ready(); self.engine.submit(self.proposal(d))
        s=self.engine.run_stage(SerialAdapter()); self.accept()
        s=self.store.load(); d=self.engine.dispatch(s['revision'],'worker','synthetic-tester')
        before=(self.target/'app.py').read_bytes(); r=envelope(d,content='# Synthetic integrated test report')
        r['delivery']={'changes':[]}; s=self.engine.submit(r)
        self.assertEqual((self.target/'app.py').read_bytes(),before)
        self.assertIn('Orchestrator-executed checks',s['artifact']['content'])

    def test_windows_aliases_cannot_address_protected_paths(self):
        from asdlc.delivery import safe_path
        for name in ('.git./hooks/x','.git /hooks/x','CON.txt','dir/LPT1','../x','C:/x','file:stream','dir/*'):
            with self.subTest(path=name):
                with self.assertRaises(GateError): safe_path(name)

    def test_partial_apply_failure_restores_prior_completed_write(self):
        from asdlc.delivery import Transaction, atomic_bytes
        d=self.ready()
        s=self.store.load()
        # Exact fixture policy gets a second approved path in the bound upstream
        # content for this utility-level failure-injection check only.
        upstream=s['inputs']['upstream'][-1]['artifact']
        upstream['content']=upstream['content'].replace('["app.py"]','["app.py", "second.py"]')
        changes=self.proposal(d)['delivery']['changes']+[dict(path='second.py',before_sha256=None,content='print("second")\n')]
        tx=Transaction(s,changes); original=(self.target/'app.py').read_bytes()
        count=[0]
        def write(path,data):
            count[0]+=1
            if count[0]==2: raise OSError('Synthetic second-write failure')
            return atomic_bytes(path,data)
        with patch('asdlc.delivery.atomic_bytes',side_effect=write):
            with self.assertRaises(OSError): tx.apply()
        tx.rollback()
        self.assertEqual((self.target/'app.py').read_bytes(),original)
        self.assertFalse((self.target/'second.py').exists())

    def test_failed_testing_returns_to_development_with_budget(self):
        d=self.ready(); self.engine.submit(self.proposal(d)); self.engine.run_stage(test_pipeline.SerialAdapter()); self.accept()
        from asdlc.delivery import CheckFailure
        s=self.store.load(); d=self.engine.dispatch(s['revision'],'worker','synthetic-tester')
        result=envelope(d,content='# Test failure report'); result['delivery']={'changes':[]}
        with patch('asdlc.delivery.execute_checks',side_effect=CheckFailure([dict(command=['fixture'],exit_code=1,stdout='',stderr='integration failure')])):
            s=self.engine.submit(result)
        self.assertEqual((s['stage'],s['status']),('development','changes_requested'))
        self.assertEqual(len(s['inputs']['upstream']),4)
        self.assertFalse(any(r['valid'] and r['state']['stage']=='development' for r in s['stage_records']))
        self.assertTrue(any('integration failure' in d['text'] for d in s['decisions']))
        self.store.resume()

    def test_test_source_mutation_cannot_validate_different_delivered_bytes(self):
        command=['{python}','-c','from pathlib import Path; Path("app.py").write_text("print(99)\\n")']
        d=self.ready(command=command); before=(self.target/'app.py').read_bytes()
        s=self.engine.submit(self.proposal(d))
        self.assertEqual(s['status'],'changes_requested')
        self.assertEqual((self.target/'app.py').read_bytes(),before)
        self.assertIn('Test modified source',s['results'][-1]['content'])

    def test_delivery_question_pauses_without_checks_or_writes(self):
        d=self.ready(); before=(self.target/'app.py').read_bytes()
        r=envelope(d,content='# Missing business choice',questions=[dict(id='Q-rule',text='Confirm addition rule?',blocking=True,answer=None)])
        r['delivery']={'changes':[]}
        with patch('asdlc.delivery.execute_checks',side_effect=AssertionError('Questions cannot run tests')):
            s=self.engine.submit(r)
        self.assertEqual(s['status'],'awaiting_input')
        self.assertEqual(s['questions'][0]['id'],'Q-rule')
        self.assertEqual((self.target/'app.py').read_bytes(),before)

    def test_transient_windows_replace_is_bounded_and_atomic(self):
        import os
        from asdlc.store import replace_file
        from pathlib import Path
        source=Path(self.tmp.name)/'source.tmp'; dest=Path(self.tmp.name)/'destination.txt'
        source.write_bytes(b'new'); dest.write_bytes(b'old'); actual=os.replace
        count=[0]
        def replace(a,b):
            count[0]+=1
            if count[0]==1: raise PermissionError('Synthetic sharing violation')
            actual(a,b)
        with patch('asdlc.store.os.replace',side_effect=replace), patch('asdlc.store.time.sleep'):
            replace_file(source,dest)
        self.assertEqual(dest.read_bytes(),b'new')
        source.write_bytes(b'pending')
        with patch('asdlc.store.os.replace',side_effect=PermissionError('Persistent denial')) as replace, patch('asdlc.store.time.sleep'):
            with self.assertRaises(PermissionError): replace_file(source,dest)
            self.assertEqual(replace.call_count,5)
        self.assertEqual(dest.read_bytes(),b'new')

    def test_rejected_result_is_retained_and_visible_on_resume(self):
        d=self.ready(); result=envelope(d,content='# Invalid worker output',verdict='pass')
        with self.assertRaises(GateError): self.engine.submit(result)
        attempts=list((self.store.folder/'attempts').glob('rejected-*.json'))
        self.assertEqual(len(attempts),1)
        retained=json.loads(attempts[0].read_text(encoding='utf-8'))
        self.assertEqual(retained['result']['run_id'],d['id'])
        self.store.resume()
        self.assertIn('prior result rejected',(self.store.folder/'project-status.md').read_text(encoding='utf-8'))

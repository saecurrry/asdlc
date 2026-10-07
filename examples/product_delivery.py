"""Separate application demonstration: synthetic gates, actual files/test processes."""
import hashlib
import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

from asdlc.adapters import envelope, CodexAdapter
from asdlc.engine import Engine, initial
from asdlc.pipeline import STAGES
from asdlc.store import Store
from asdlc.code_version import capture


class SampleAdapter:
    def stage(self, d, s, prompts):
        if d['kind']=='review':
            return envelope(d, verdict='pass',summary='SYNTHETIC reviewer; not real independent Codex review',
                            code_version=capture(s['config']['target']) if s['stage'] in ('development','testing','sprint-review') else None)
        result=envelope(d,content='# Synthetic '+s['stage'],summary='SYNTHETIC documentation; application/tests actually executed')
        if s['stage']=='business-requirements':
            result['content']+='\n```asdlc-artifacts\n'+json.dumps([
                dict(id='I1',type='initiative',parent=None,content='# I1\nReliable integer addition for sample users.'),
                dict(id='E1',type='epic',parent='I1',content='# E1\nR1: add positive, zero and negative integers correctly.')])+'\n```'
        if s['stage']=='sprint-planning':
            result['content']+='\n```asdlc-artifacts\n'+json.dumps([dict(id='S1',type='story',parent='E1',content='# S1\nImplement add(a,b). Verify positive, zero and negative examples using unittest.')])+'\n```'
            result['content']+='\n```asdlc-delivery\n'+json.dumps(dict(write_paths=['calculator.py','test_calculator.py'],test_commands=[['{python}','-m','unittest','discover','-v']]))+'\n```'
        if s['stage']=='development':
            source='def add(a, b):\n    return a + b\n'
            checks='import unittest\nfrom calculator import add\nclass AdditionTests(unittest.TestCase):\n    def test_positive(self): self.assertEqual(add(2,3),5)\n    def test_negative(self): self.assertEqual(add(-2,-3),-5)\n    def test_zero(self): self.assertEqual(add(0,0),0)\n'
            result['delivery']=dict(changes=[dict(path=name,before_sha256=None,content=text) for name,text in [('calculator.py',source),('test_calculator.py',checks)]])
        elif s['stage']=='testing': result['delivery']=dict(changes=[])
        elif s['stage']=='sprint-review': result['code_version']=capture(s['config']['target'])
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-delivery',action='store_true',help='Use actual installed Codex for delivery specialists/reviewers; earlier artifacts and every approval remain synthetic')
    parser.add_argument('--resume-run',help='Resume a retained sample run without resetting state or repeating accepted stages')
    args=parser.parse_args()
    base=Path('.asdlc-local/product-demonstrations').resolve()
    root=Path(args.resume_run).resolve() if args.resume_run else base/uuid.uuid4().hex
    if not root.is_relative_to(base): raise ValueError('Sample run must remain within its fixture area')
    app=root/'application'
    if not args.resume_run:
        app.mkdir(parents=True)
        subprocess.run(['git','init',str(app)],check=True,capture_output=True)
        (app/'README.md').write_text('# Synthetic calculator product fixture\n',encoding='utf-8')
    wiki=root/'fixture-wiki'; store=Store(wiki,'calculator-fixture')
    if not args.resume_run:
        store.create(initial('calculator-fixture',app,wiki,True,'Synthetic integer addition application; tests cover positives, negatives, zero. No live approvals.',pipeline=True))
    elif not store.load()['config']['fixture']:
        raise ValueError('Only explicitly synthetic projects can use fixture approvals')
    engine=Engine(store); pauses=[]
    codex=CodexAdapter() if args.codex_delivery else None
    for stage in STAGES:
        current=store.load()
        if any(r['valid'] and r['state']['stage']==stage for r in current['stage_records']):
            snap=next(r['state'] for r in current['stage_records'] if r['valid'] and r['state']['stage']==stage)
            pauses.append(dict(stage=stage,revision=snap['revision'],artifact_hash=snap['artifact']['hash']))
            continue
        print('Running '+stage,flush=True)
        state=engine.run_stage(codex if codex and stage in ('development','testing','sprint-review') else SampleAdapter())
        if state['stage']!=stage or state['status']!='awaiting_approval':
            print(json.dumps(dict(stopped_at=stage,status=state['status'],state=str(store.path.resolve())),indent=2))
            return
        pauses.append(dict(stage=stage,revision=state['revision'],artifact_hash=state['artifact']['hash']))
        # Explicitly synthetic, never impersonates the human project owner.
        engine.approve(state['revision'],state['artifact']['hash'],'synthetic-fixture-approval')
        resumed=subprocess.run([sys.executable,'-m','asdlc','--wiki',str(wiki),'--project','calculator-fixture','resume'],capture_output=True,text=True,check=True)
        assert json.loads(resumed.stdout)['revision']==store.load()['revision']
    state=store.load()
    evidence=dict(kind='SYNTHETIC DOCUMENTATION/REVIEWS/APPROVALS; REAL LOCAL CODE AND TEST EXECUTION',seven_gate_pauses=pauses,
                  code_version=capture(app),final_status=state['status'],real_codex_execution=args.codex_delivery,live_human_acceptance=False,
                  files={name:hashlib.sha256((app/name).read_bytes()).hexdigest() for name in ('calculator.py','test_calculator.py')},
                  separate_artifacts=[str(p.relative_to(store.folder)) for p in store.folder.rglob('*.md') if p.parent.name in ('initiatives','epics','stories')])
    path=root/'evidence.json'; path.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(path.resolve())


if __name__=='__main__': main()

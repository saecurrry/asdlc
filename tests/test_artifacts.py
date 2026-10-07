import json
import unittest
import test_pipeline
from asdlc.adapters import envelope
from asdlc.store import GateError


class ArtifactTests(unittest.TestCase):
    setUp = test_pipeline.PipelineTests.setUp
    tearDown = test_pipeline.PipelineTests.tearDown
    accept = test_pipeline.PipelineTests.accept

    def test_individual_artifacts_render_and_tamper_is_rejected(self):
        self.engine.run_stage(test_pipeline.SerialAdapter()); self.accept()
        s=self.store.load(); d=self.engine.dispatch(s['revision'],'worker','synthetic-business-author')
        values=[dict(id='I1',type='initiative',parent=None,content='# Outcome initiative'),
                dict(id='E1',type='epic',parent='I1',content='# Requirement epic')]
        s=self.engine.submit(envelope(d,content='# BRD\n```asdlc-artifacts\n'+json.dumps(values)+'\n```'))
        self.assertTrue((self.store.folder/'requirements/initiatives/i1.md').exists())
        self.assertTrue((self.store.folder/'requirements/epics/e1.md').exists())
        version=next((self.store.folder/'requirements/epics').glob('e1-*.md'))
        version.write_text('tampered')
        with self.assertRaises(GateError): self.store.resume()

    def test_missing_parent_and_wrong_stage_refuse_inventory(self):
        self.engine.run_stage(test_pipeline.SerialAdapter()); self.accept()
        s=self.store.load(); d=self.engine.dispatch(s['revision'],'worker','synthetic-business-author')
        for value in [dict(id='E1',type='epic',parent='missing',content='# Epic'),
                      dict(id='S1',type='story',parent='E1',content='# Story')]:
            with self.assertRaises(GateError): self.engine.submit(envelope(d,content='```asdlc-artifacts\n'+json.dumps([value])+'\n```'))

    def test_upstream_identity_cannot_be_reused_by_story(self):
        from asdlc.artifacts import validate_inventory
        state={'stage':'sprint-planning','inputs':{'upstream':[{'artifact':{'content':'```asdlc-artifacts\n'+json.dumps([dict(id='I1',type='initiative',parent=None,content='Outcome'),dict(id='E1',type='epic',parent='I1',content='Epic')])+'\n```'}}]}}
        with self.assertRaises(GateError): validate_inventory(state,'```asdlc-artifacts\n'+json.dumps([dict(id='I1',type='story',parent='E1',content='Story')])+'\n```')

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from incident_agent import engine, client
ROOT = Path(__file__).resolve().parents[1]


def model_result(incident='INC-004'):
    return {'status':'supported','cause':'memory limit regression','explanation':'The lower limit correlates with OOMKilled terminations.',
            'evidence_ids':[incident+'-METRIC',incident+'-TRACE',incident+'-CHANGE'],
            'alternative':'A traffic surge is possible but not supported by the supplied evidence.',
            'recommendation':'Review restoring the container memory limit after human approval.'}

class InvestigatorTests(unittest.TestCase):
    def test_real_failure_reproduced_in_preserved_original(self):
        spec=importlib.util.spec_from_file_location('original',ROOT/'evidence/regression/original_engine.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        self.assertEqual(old.investigate('Why did inventory-service restart during INC-004?')['status'],'refused')

    def test_diagnostic_regression_reaches_model_with_candidate_setting(self):
        settings=json.loads((ROOT/'config/settings.json').read_text());settings['guard_mode']='diagnostic-aware-v2'
        original=Path.read_text
        def read(path,*a,**kw):
            if path == ROOT/'config/settings.json': return json.dumps(settings)
            return original(path,*a,**kw)
        with patch.object(Path,'read_text',read), patch.object(engine,'complete',return_value=(model_result(),{'input_tokens':100,'output_tokens':50})) as call:
            result=engine.investigate('Why did inventory-service restart during INC-004?')
        self.assertEqual(result['status'],'ok');call.assert_called_once()
        self.assertIn('memory limit regression',result['text'])

    def test_actions_and_mixed_requests_still_refused(self):
        for q in ['Restart inventory-service','Please restart inventory-service','Why did inventory restart? Then restart it.','Why did inventory restart and delete logs?']:
            self.assertTrue(engine.blocked(q,'diagnostic-aware-v2'),q)
        self.assertFalse(engine.blocked('Why did inventory-service restart during INC-004?','diagnostic-aware-v2'))

    def test_unknown_and_ambiguous_never_call_model(self):
        with patch.object(engine,'complete') as call:
            for q in ['INC-999','INC-001 and INC-002','INC-001 and INC-999','unknown-service']:
                self.assertEqual(engine.investigate(q)['status'],'unknown')
            call.assert_not_called()

    def test_payload_excludes_ground_truth_and_redacts(self):
        incident=engine.retrieve('INC-004')
        payload=engine.payload_for('INC-004 token=example-value',incident,json.loads((ROOT/'manifest.json').read_text()),json.loads((ROOT/'config/settings.json').read_text()))
        self.assertNotIn('hypotheses',payload['input']);self.assertNotIn('supports',payload['input'])
        self.assertNotIn('example-value',payload['input']);self.assertFalse(payload['store'])
        self.assertNotIn('tools',payload)

    def test_unknown_citations_rejected(self):
        r=model_result();r['evidence_ids'].append('FAKE')
        with patch.object(engine,'complete',return_value=(r,{})):
            with self.assertRaisesRegex(client.ModelError,'citation'):engine.investigate('INC-004')

    def test_free_text_citations_rejected(self):
        r=model_result();r['explanation']+=' [FAKE]'
        with patch.object(engine,'complete',return_value=(r,{})):
            with self.assertRaisesRegex(client.ModelError,'Citation'):engine.investigate('INC-004')

    def test_model_abstention(self):
        r=model_result();r['status']='insufficient';r['evidence_ids']=[]
        with patch.object(engine,'complete',return_value=(r,{})):
            self.assertEqual(engine.investigate('INC-004')['status'],'unknown')

    def test_missing_key_fails_instead_of_mock_fallback(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaisesRegex(client.ModelError,'OPENAI_API_KEY'):engine.investigate('INC-001')

    def test_responses_http_contract(self):
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(model_result())}]}],'usage':{'input_tokens':9,'output_tokens':8}}
        handle=MagicMock();handle.__enter__.return_value.read.return_value=json.dumps(response).encode()
        with patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}), patch.object(client,'urlopen',return_value=handle) as call:
            report,usage=client.complete({'model':'test'},45)
        request=call.call_args.args[0]
        self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
        self.assertEqual(json.loads(request.data),{'model':'test'})
        self.assertEqual(report,model_result());self.assertEqual(usage['output_tokens'],8)

    def test_http_error_does_not_echo_credentials(self):
        with patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}), patch.object(client,'urlopen',side_effect=HTTPError('url',401,'sensitive',{},None)):
            with self.assertRaisesRegex(client.ModelError,'HTTP 401') as result:client.complete({},45)
        self.assertNotIn('sensitive',str(result.exception))

    def test_incomplete_response_fails(self):
        handle=MagicMock();handle.__enter__.return_value.read.return_value=b'{"status":"incomplete"}'
        with patch.dict('os.environ',{'OPENAI_API_KEY':'unit-test-placeholder'}),patch.object(client,'urlopen',return_value=handle):
            with self.assertRaisesRegex(client.ModelError,'not completed'):client.complete({},45)

class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dst=Path(self.tmp.name)/'project'
        shutil.copytree(ROOT,self.dst,ignore=shutil.ignore_patterns('.git','__pycache__','reference','reports'))
        for p in ['baseline.json','gate_report.json']:
            (self.dst/p).unlink(missing_ok=True)
        (self.dst/'system.py').write_text('def answer(question, seed=0):\n    return "safe answer [TEST]"\n')
        cases=[{'id':'one','category':'safety','question':'q','checks':[['cites','TEST']]},{'id':'two','category':'diagnosis','question':'q','checks':[['contains','safe']]}]
        (self.dst/'eval_set.jsonl').write_text('\n'.join(json.dumps(c) for c in cases)+'\n')
        self.refresh()
    def runcommand(self,*args):
        return subprocess.run([sys.executable,*args],cwd=self.dst,text=True,capture_output=True)
    def refresh(self):
        result=self.runcommand('scripts/release.py');self.assertEqual(result.returncode,0,result.stderr)
    def baseline(self):
        result=self.runcommand('eval_gate.py','--aa');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_ship_then_real_output_regression_blocks(self):
        self.baseline()
        self.assertEqual(self.runcommand('eval_gate.py','--gate').returncode,0)
        (self.dst/'system.py').write_text('def answer(question, seed=0):\n    return "broken"\n');self.refresh()
        result=self.runcommand('eval_gate.py','--gate')
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertIn('critical category safety',result.stdout)
    def test_execution_error_cannot_create_baseline(self):
        (self.dst/'system.py').write_text('def answer(question, seed=0):\n    raise RuntimeError("API unavailable")\n');self.refresh()
        result=self.runcommand('eval_gate.py','--aa')
        self.assertEqual(result.returncode,2);self.assertFalse((self.dst/'baseline.json').exists())
        self.assertIn('Execution errors',result.stderr)
    def test_hash_mismatch_blocks_before_model(self):
        self.baseline()
        with (self.dst/'eval_set.jsonl').open('a') as f:f.write(json.dumps({'id':'new','category':'diagnosis','question':'q','checks':[['contains','safe']]})+'\n')
        self.refresh();r=self.runcommand('eval_gate.py','--gate')
        self.assertEqual(r.returncode,2);self.assertIn('Baseline eval-set hash mismatch',r.stderr)
    def test_stale_artifact_blocks(self):
        with (self.dst/'system.py').open('a') as f:f.write('\n# change\n')
        r=self.runcommand('eval_gate.py','--aa')
        self.assertEqual(r.returncode,2);self.assertIn('stale',r.stderr)

if __name__=='__main__':unittest.main()

"""Generate the HW6 submission from measured evidence; reportlab is authoring-only."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import statistics
import subprocess
import textwrap
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, default=ROOT/'reports/HW6_Report.pdf')
a = p.parse_args()
a.output.parent.mkdir(parents=True, exist_ok=True)
def read(path):return json.loads((ROOT/path).read_text())
meta = read('docs/submission_metadata.json')
base = read('baseline.json')
gate = read('evidence/live/gate/gate_report.json')
manifest = gate['manifest']
cases = [json.loads(x) for x in (ROOT/'eval_set.jsonl').read_text().splitlines() if x.strip()]
hashes = read('evidence/regression/hashes.json')
base_runs = [json.loads(x) for x in (ROOT/'evidence/live/aa/eval_results.jsonl').read_text().splitlines() if x.strip()]
candidate_runs = [json.loads(x) for x in (ROOT/'evidence/live/gate/eval_results.jsonl').read_text().splitlines() if x.strip()]
assert gate['eval_set_hash'] == base['eval_set_hash'] == manifest['eval_set_hash']
assert len(base_runs) == 10 and len(candidate_runs) == 5
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName='Helvetica', fontSize=9.2, leading=13.4, spaceAfter=8, textColor=colors.HexColor('#233649')))
styles.add(ParagraphStyle(name='CodeReport', fontName='Courier', fontSize=7.2, leading=9.2))
styles.add(ParagraphStyle(name='CellReport', fontName='Helvetica', fontSize=8.1, leading=10.8, spaceAfter=2))
styles['Title'].textColor=colors.HexColor('#12344A')
styles['Heading1'].textColor=colors.HexColor('#12344A')
styles['Heading2'].textColor=colors.HexColor('#12344A')
story=[]
def para(t):story.append(Paragraph(escape(str(t)),styles['BodyReport']))
def link(label,url):story.append(Paragraph(escape(label)+': <link href="'+escape(url,quote=True)+'" color="#146388">'+escape(url)+'</link>',styles['BodyReport']))
def heading(t):story.append(Paragraph(escape(t),styles['Heading1']))
def sub(t):story.append(Paragraph(escape(t),styles['Heading2']))
def code(t,width=94):
 lines=[]
 for line in t.splitlines():lines.extend(textwrap.wrap(line,width=width,replace_whitespace=False,drop_whitespace=False) or [''])
 story.append(Preformatted('\n'.join(lines),styles['CodeReport']));story.append(Spacer(1,8))
def table(rows,widths):
 data=[[Paragraph(escape(str(c)),styles['CellReport']) for c in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDF3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#CCD7DF')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 story.append(t);story.append(Spacer(1,11))
def new():story.append(PageBreak())
def pct(x):return f'{100*x:.1f}%'
def pp(x):return f'{100*x:.1f} pp'
def casepasses(runs,id):return sum(int(r['rows'][id]['pass']) for r in runs)
def clean_output(path):
 return '\n'.join(x for x in (ROOT/path).read_text().splitlines() if not x.startswith('Completed run '))

story.append(Paragraph('HW6 | An LLMOps pipeline for our project',styles['Title']))
para('Enterprise AI Incident Response Agent - CMPE 297')
para('Michael Kennedy and Alekya Gudise | October 26, 2026 (America/Los_Angeles)')
heading('1. Release result')
para('Verdict: '+gate['verdict']+'. The pre-change release averaged '+pct(base['mean']['overall'])+' overall across ten A/A runs; the candidate averaged '+pct(gate['candidate']['overall'])+' across five fresh runs. Both used the same 41-case evaluation set, hash '+gate['eval_set_hash']+'.')
for reason in gate['reasons']:para('Gate reason: '+reason)
para('The real release change is guard_mode: legacy-keyword-v1 -> diagnostic-aware-v2. It permits narrowly scoped questions about why a service restarted, while continuing to refuse action requests. The model, prompt and evaluation expectations were held fixed.')
link('Repository',meta['repository_url'])
link('Candidate pull request',meta['pull_request_url'])
link('Candidate CI run',meta['ci_run_url'])
link('Baseline CI run',meta['baseline_ci_run_url'])
para('Baseline measured source commit: '+meta['baseline_measured_commit'])
para('Baseline committed at: '+meta['baseline_commit'])
para('Candidate tested head commit: '+meta['tested_commit'])
sub('System boundary')
para('A single-model investigator retrieves synthetic metrics, traces, deployment changes and runbooks by incident ID or service name, sends only evidence to a pinned model, validates the structured response and citation IDs, and returns a cited diagnosis. Ground-truth labels are stored separately and are never loaded by the runtime. No tools can change the investigated services.')
para('This is a local project prototype, not a deployed production platform. The baseline is its measured pre-change reference release. The results below are hosted-model measurements, distinct from the earlier deterministic prototype and the instructor catalog example.')
new();heading('2. Evaluation set and scoring')
counts=Counter(c['category'] for c in cases)
table([['Category','Cases','Critical?']]+[[k,v,'Yes' if k in manifest['gate']['critical'] else 'No'] for k,v in sorted(counts.items())],[270,90,156])
para('The 41 cases cover four synthetic incidents: checkout database connection pool exhaustion, payment provider timeout, catalog cache disablement, and inventory memory-limit regression. Safety is the small critical category: all four cases must pass in every candidate run.')
para('Diagnosis checks are anchored to the model-generated Likely cause line. Evidence cases additionally require a relevant evidence ID on that line; quoting a correct input record elsewhere cannot satisfy the diagnosis. Recommendation and hypothesis cases require the expected report features plus a plausible diagnosis. These are pattern-based checks, not a complete semantic judge.')
sub('Three examples from eval_set.jsonl')
for id in ['INC-001-diagnosis-1','policy-1','regression-diagnostic-restart']:
 c=next(c for c in cases if c['id']==id)
 para(c['id']+' | '+c['category']+' | '+c['question'])
 code('Checks: '+json.dumps(c['checks']),92)
para('The evaluated hash is '+manifest['eval_set_hash']+'. Expectations were fixed before live execution; no cases were weakened or rewritten to make the release pass.')
new();heading('3. Noise floor: ten A/A runs')
para('Command: python eval_gate.py --aa. The baseline was measured before the candidate settings change, committed to main, and inherited unchanged by the candidate. For each category the comparison sigma is population run SD multiplied by sqrt(2/5). Values below are percentages; SD and sigma are percentage points.')
rows=[['Category','Mean','Min-max','Run SD','Sigma']]
for k in sorted(base['sigma']):
 s=base['spread'][k];rows.append([k,pct(base['mean'][k]),pct(s['min'])+' - '+pct(s['max']),pp(base['run_sd'][k]),pp(base['sigma'][k])])
table(rows,[115,65,136,100,100])
sub('Captured --aa output')
code(clean_output('evidence/live/aa/output.txt'),102)
para('Full output, per-case responses, API usage and the exact baseline manifest are committed under evidence/live/aa/. The original baseline artifact is baseline.json. The missing-key setup error from an earlier attempt remains preserved separately and is not used as measurement data.')
new();heading('4. Real change through the PR gate')
para('The CI workflow checks each pull request, runs local tests, validates artifact hashes, restores baseline.json from the PR base commit, and executes python eval_gate.py --gate. It uploads the report and per-case results even when the gate blocks.')
para('Gate settings: runs=5; max_drop_sigma=3; max_token_increase=0.20; critical=[safety]. Rationale: three measured comparison standard deviations allows ordinary sampling variation while flagging larger quality drops, and 20% allows modest response-length variation while blocking a material increase in the starter token proxy. These are engineering thresholds, not a formal statistical guarantee from ten baseline runs.')
sub('Captured candidate output')
code(clean_output('evidence/live/gate/output.txt'),102)
link('Pull request',meta['pull_request_url'])
link('CI run',meta['ci_run_url'])
para('Interpretation: '+meta['result_interpretation'])
para('These are frozen automated-check scores, not calibrated diagnosis accuracy; evaluator false negatives are analyzed on the operations/limitations page.')
para('The token gate uses the instructor characters/4 estimate of final answer length. It is not billed model usage; input/output API tokens are separately recorded. A BLOCK is retained as a valid homework finding rather than changing the evaluation or regenerating a more favorable baseline.')
new();heading('5. Regression from an observed project failure')
q='Why did inventory-service restart during INC-004?'
para('During development on October 26, the original prototype incorrectly refused this valid diagnostic question: '+q)
para('Actual old behavior: '+read('evidence/regression/observed_failure.json')['actual']['text'])
para('Cause: the guard treated any occurrence of restart as an action request. The preserved original engine reproduces this observed local defect. This was a real development failure, not a claimed earlier production incident.')
para('The new case regression-diagnostic-restart requires a memory-related cause and excludes [POLICY]. The candidate changes a versioned guard setting to permit narrow diagnostic prefixes; imperative, mixed-action and credential requests remain refused. The before/after counts below are taken from the live evaluation logs.')
id='regression-diagnostic-restart'
table([['Measurement','Regression passes'],['Pre-change A/A',f'{casepasses(base_runs,id)}/10'],['Candidate gate',f'{casepasses(candidate_runs,id)}/5']],[300,216])
sub('One actual candidate response')
para(candidate_runs[0]['rows'][id]['answer'])
table([['Evaluation revision','Cases','Hash'],['Before adding this case','40',hashes['llm_eval_before_regression']],['After adding this case','41',hashes['llm_eval_after_regression']],['Earlier offline prototype (different eval)','40',hashes['legacy_prototype']]],[290,60,166])
para('evidence/regression/eval_before.jsonl preserves the exact 40-case LLM set. Adding only this regression yields the 41-case hash used by both live releases. The separate migration from the earlier offline system is not presented as a one-case change.')
new();heading('6. Proposed production alert and rollback')
para((ROOT/'docs/RUNBOOK.md').read_text().split('\n\n',1)[1].strip())
sub('Observed usage, without a billing claim')
def usage(runs):
 rows=[v for r in runs for v in r['rows'].values()]
 calls=[r['metrics'] for r in rows if r.get('metrics',{}).get('model_calls')]
 return [len(calls),sum(m.get('input_tokens',0) for m in calls),sum(m.get('output_tokens',0) for m in calls),round(statistics.median(m.get('latency_ms',0) for m in calls)) if calls else 0]
table([['Run group','Model calls','Input tokens','Output tokens','Median ms'],['A/A',*usage(base_runs)],['Candidate',*usage(candidate_runs)]],[100,100,106,110,100])
para('These totals exclude the smoke call and count the successful recorded evaluations. No API key is stored in source or reports. GitHub injects OPENAI_API_KEY from a repository secret. Runtime limits include one model call per supported question, no automatic retries, a 45-second request timeout and a 1,800-token output cap.')
sub('Limitations and failure analysis')
para(meta['failure_analysis'])
para('Example: the model wrote The deployment disabled the cache by changing CACHE_ENABLED from true to false. The original pattern expects cache before disabl/off/config, so that supported diagnosis fails. Fixing this scorer requires a separately versioned eval and remeasurement of the pre-change release; it was not changed during this comparison.')
para('Four synthetic incidents do not establish real-world generalization. Citation-ID validation checks that an ID exists, not whether every claim is entailed. Keyword guards and redaction are limited to this prototype. The project has no live service connectors, semantic retrieval, dashboard, multi-agent comparison or deployed paging integration yet.')
new();heading('7. Complete candidate release manifest')
para('The exact manifest below is the one emitted by the tested candidate CI run. Answer-changing code, evidence, prompt, settings, tool definitions and output schema are versioned by SHA-256. The baseline manifest is stored inside baseline.json. The candidate differs in release label and guard setting/hash; evaluation, model and prompt remain fixed.')
code(json.dumps(manifest,indent=2),100)
new();heading('8. Reproducibility and implementation notes')
sub('Instructor starter exercise')
para('The original catalog starter was run as shipped in an isolated copy. Its unchanged candidate returned SHIP; changing prompt_version to v2 returned BLOCK. Its ten-run overall mean was 88.3%, spread 66.7%-100.0%, and comparison sigma 6.7 percentage points. The toy results are separate from all incident-investigator measurements. See evidence/starter/transcript.txt.')
sub('Changes to eval_gate.py')
para('The scoring rules and sigma formula remain intact. Documented fixes validate manifest artifact hashes, reject mismatched evaluation/baseline hashes instead of merely warning, reject incompatible category/run counts, abort on execution errors so outages cannot become zero-quality baselines, remove stale report files, reject invalid run counts or empty evaluations, and log per-case answers, usage, latency and min/max spread.')
sub('Evidence inventory')
table([['File or folder','Purpose'],['baseline.json','Committed ten-run reference baseline, including manifest and sigma'],['evidence/live/aa/','A/A console output and ten runs of per-case evidence'],['evidence/live/gate/','Candidate verdict, console output and five runs of per-case evidence'],['evidence/regression/','Original failure, preserved old engine, before/after eval hashes'],['manifest.json; eval_set.jsonl','Release identity and fixed evaluation cases'],['.github/workflows/','Manual baseline workflow and pull-request gate'],['docs/RUNBOOK.md','Proposed alert, named responder and release rollback procedure']],[190,326])
para('Sixteen local unit/contract tests passed in CI. They cover the old false refusal, candidate diagnostic routing, action refusal, unknown incidents, label exclusion/redaction, citation validation, API failures and gate integrity. Mocked tests establish integration behavior; the live measurements establish this evaluation result.')
para('For reproduction, check out the recorded measured source commits. Set the API key through a secret, run the baseline on the pre-change version, then evaluate the candidate with that same baseline and eval set. Hosted model variability means a later rerun need not reproduce identical scores.')
para('Submission: Michael Kennedy and Alekya Gudise should upload the same PDF. The PR remains open for review; passing the gate is not a claim of production deployment.')
sub('Sources')
para('Assignment and project proposal: user-supplied PDFs. Original source documents are retained locally under reference/.')
link('Responses structured output contract','https://developers.openai.com/api/docs/guides/structured-outputs')
link('Pinned model documentation','https://developers.openai.com/api/docs/models/gpt-5.4-mini')
def page(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#CCD7DF'));canvas.line(48,40,564,40)
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536878'))
 canvas.drawString(48,27,'CMPE 297 | HW6 | Michael Kennedy and Alekya Gudise')
 canvas.drawRightString(564,27,str(doc.page))
SimpleDocTemplate(str(a.output),pagesize=(612,792),rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=52,title='HW6 LLMOps Pipeline - Measured Release Report',author='Michael Kennedy and Alekya Gudise').build(story,onFirstPage=page,onLaterPages=page)
print(a.output)

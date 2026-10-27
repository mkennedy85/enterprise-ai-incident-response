"""Build the HW6 evidence report. Requires reportlab only for PDF authoring."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import subprocess
import textwrap
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/HW6_Report_DRAFT.pdf');args=p.parse_args()
args.output.parent.mkdir(parents=True,exist_ok=True)
meta=json.loads((ROOT/'docs/submission_metadata.json').read_text())
manifest=json.loads((ROOT/'manifest.json').read_text())
cases=[json.loads(l) for l in (ROOT/'eval_set.jsonl').read_text().splitlines() if l.strip()]
hashes=json.loads((ROOT/'evidence/regression/hashes.json').read_text())
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='SmallBody',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=8,textColor=colors.HexColor('#243247')))
styles.add(ParagraphStyle(name='CodeSmall',fontName='Courier',fontSize=7,leading=9))
styles['Title'].textColor=colors.HexColor('#12344A');styles['Heading1'].textColor=colors.HexColor('#12344A')
story=[]
def para(t):story.append(Paragraph(escape(t),styles['SmallBody']))
def heading(t):story.append(Paragraph(escape(t),styles['Heading1']))
def code(t,width=94):
 lines=[]
 for line in t.splitlines():lines.extend(textwrap.wrap(line,width=width,replace_whitespace=False,drop_whitespace=False) or [''])
 story.append(Preformatted('\n'.join(lines),styles['CodeSmall']));story.append(Spacer(1,9))
def table(rows,widths):
 data=[[Paragraph(escape(str(c)),styles['SmallBody']) for c in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDF3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#CCD7DF')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def new():story.append(PageBreak())
def textfile(path,default):
 q=ROOT/path;return q.read_text() if q.exists() else default

story.append(Paragraph('HW6 | LLMOps release pipeline',styles['Title']))
para('Enterprise AI Incident Response Agent - CMPE 297')
para(meta['submission_status'])
para('Prepared October 26, 2026 (America/Los_Angeles). Team: '+(', '.join(meta['team_members']) or 'PENDING - enter all team members.'))
heading('1. System and completion status')
para('A minimal single-model investigator retrieves synthetic metric, trace, deployment and runbook records, asks a pinned OpenAI model for a structured diagnosis, validates citation IDs, and returns read-only recommendations. Ground-truth hypothesis labels are stored separately and never loaded by the runtime.')
para('The runtime uses the standard library and the Responses API. It exposes no remediation tools. This is a controlled local prototype, not a deployed multi-agent platform or production monitoring service.')
table([['Requirement','Status'],['Manifest, model adapter, 41-case evaluation','Implemented; model access not yet verified'],['Starter exercise and regression','Starter SHIP/BLOCK observed; real false refusal captured'],['Local unit/contract tests','16 passed; mocked responses are not live model evidence'],['LLM A/A and candidate gate','Pending API key; missing-key error preserved'],['GitHub repository, PR and CI links','Pending repository destination and Actions secret'],['Runbook and report','Proposed runbook complete; this PDF remains a draft']],[230,270])
para('Repository: '+meta['repository_url'])
para('Local source commit used to generate this report: '+commit)
para('Final tested CI commit: '+meta['tested_commit'])
para('The archived offline 100% baseline does not represent LLM performance. No live score, noise floor, or successful CI run is claimed in this draft.')
new();heading('2. Evaluation set')
counts=Counter(c['category'] for c in cases)
table([['Category','Cases','Critical?']]+[[k,v,'Yes' if k in manifest['gate']['critical'] else 'No'] for k,v in sorted(counts.items())],[250,100,150])
para('Total: '+str(len(cases))+'. Canonical content hash: '+manifest['eval_set_hash']+'. Only safety is critical; every safety case must pass in each of the five comparison runs.')
para('Diagnosis checks are anchored to the model-generated cause line. Evidence checks require the expected citation on that line, so merely quoting input evidence cannot satisfy the diagnosis. Case expectations were fixed before live model execution. The checks remain heuristic and do not prove semantic entailment.')
heading('Three example cases')
for id in ['INC-001-diagnosis-1','policy-1','regression-diagnostic-restart']:
 c=next(c for c in cases if c['id']==id)
 code(json.dumps(c,indent=2),90)
new();heading('3. A/A measurement and candidate gate')
para('Gate: five runs, max_drop_sigma=3, max_token_increase=0.20. Three measured standard deviations tolerates ordinary sampling variability; a 20% answer-length increase permits modest variation while flagging a material cost proxy increase. These are engineering thresholds, not a statistical guarantee.')
para('A/A requires ten independent runs of the pre-change main release on the same 41 cases as the candidate. Report category means, min/max, run standard deviation and comparison sigma. A zero sigma is reported honestly; noncritical degradation then blocks. Actual API token usage and latency are logged separately from the starter characters/4 token proxy.')
para('Live baseline output:')
code(textfile('evidence/live/aa/output.txt','PENDING - no hosted-model A/A measurement.'))
para('Live candidate output:')
code(textfile('evidence/live/gate/output.txt','PENDING - no hosted-model candidate verdict.'))
para('Actual setup attempt (not a measurement):')
code(textfile('evidence/setup/missing_key.txt','PENDING - setup capture not yet written.'),90)
para('Pull request: '+meta['pull_request_url']);para('CI run: '+meta['ci_run_url'])
heading('Instructor starter exercise - separate toy system')
para('The shipped catalog starter was executed first in an isolated copy. A/A overall spread was 66.7%-100.0%, mean 88.3%, comparison sigma 6.7%. Its unchanged candidate SHIP result was 83.3%; changing prompt_version to v2 produced BLOCK at 66.7%, with a 21.7 percentage-point drop (3.2 sigma). Full category output is in evidence/starter/transcript.txt. These are not incident-investigator results.')
new();heading('4. Real regression and release change')
para('Observed during development on October 26, 2026: "Why did inventory-service restart during INC-004?" incorrectly returned the policy refusal. The old guard treated the word restart as an action request even in a question asking for a diagnosis. The original engine and observed output are preserved in evidence/regression/. This was a real local development failure, not a claimed earlier production incident.')
code('Actual: I cannot answer requests to expose secrets, override instructions, or execute changes. Investigation is read-only; human approval is required for remediation. [POLICY]',90)
para('The candidate changes guard_mode from legacy-keyword-v1 to diagnostic-aware-v2. Diagnostic prefixes are allowed while imperative and mixed action requests remain refused. The model, prompt and eval expectations stay fixed. The regression case requires a memory-related diagnosis and excludes [POLICY]. Local tests demonstrate routing through the mocked model; the actual model answer still needs measurement.')
table([['Evaluation version','Cases','Hash'],['Before adding regression','40',hashes['llm_eval_before_regression']],['After adding regression','41',hashes['llm_eval_after_regression']],['Earlier deterministic prototype','40',hashes['legacy_prototype']]],[250,70,180])
heading('5. Proposed production runbook')
para((ROOT/'docs/RUNBOOK.md').read_text().split('\n\n',1)[1].strip())
new();heading('6. Complete release manifest')
para('SHA-256 artifact hashes below cover answer-changing code, evidence, prompt, settings, schema and tool definitions. The eval hash uses the instructor canonicalization. The manifest is validated before measurement. The exact model snapshot is gpt-5.4-mini-2026-03-17; account availability is pending a smoke call.')
code(json.dumps(manifest,indent=2),99)
new();heading('7. Evidence, limitations and submission checklist')
para('The gate retains the instructor scoring rules and sigma formula, with documented correctness fixes: artifact validation; hard rejection of baseline/eval mismatch and incompatible runs/categories; abort on execution errors; per-case answers/usage/latency logs; spread capture; and removal of stale reports. See docs/EVALUATION.md for details.')
para('CI runs tests and the gate on every pull request. It restores baseline.json from the PR base commit rather than trusting a baseline changed by the candidate. Missing API credentials or a missing baseline produces an explicit failure. The workflow is implemented but has not executed on GitHub.')
heading('Local verification')
para('Sixteen unit/contract tests passed. They cover the actual old false refusal, diagnostic routing, imperative safety, unknown incidents, label exclusion/redaction, citation validation, model abstention, missing credentials, Responses parsing, HTTP errors, incomplete responses, gate SHIP/BLOCK, invalid baselines and stale artifacts. These tests use mocked HTTP/model responses; they do not measure model quality.')
heading('Complete before submission')
for t in ['Choose the GitHub repository and visibility; configure OPENAI_API_KEY locally and as an Actions secret.', 'Measure and commit the main baseline; merge it into the candidate; run the real candidate gate without replacing the baseline.', 'Publish the candidate PR, capture the CI run, and preserve the output even if it blocks or fails.', 'Fill team names, repository, tested commit, PR and CI URLs in docs/submission_metadata.json; regenerate and inspect the PDF.', 'Every team member uploads the same final PDF. If execution remains blocked, explicitly include the attempted commands and real errors.']:para(t)
heading('Scope limitations')
para('Four synthetic incidents do not establish generalization. Root-cause and citation checks are limited pattern checks; citation existence is not proof of causal support. Redaction and keyword guards are a prototype, not a general security boundary. There is no deployed alert, dashboard, multi-agent comparison or live service integration. A new model snapshot requires a new measured release baseline.')
heading('Sources')
para('Assignment: Homework 6: an LLMOps pipeline for your project.pdf, supplied by the user. Project scope: Enterprise AI Incident Response Agent Proposal, supplied by the user.')
para('API structured output contract: https://developers.openai.com/api/docs/guides/structured-outputs')
para('Pinned model and supported features: https://developers.openai.com/api/docs/models/gpt-5.4-mini')
def page(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#CCD7DF'));canvas.line(48,40,564,40)
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536878'))
 canvas.drawString(48,27,'CMPE 297 | HW6 | Evidence report - DRAFT')
 canvas.drawRightString(564,27,str(doc.page))
SimpleDocTemplate(str(args.output),pagesize=(612,792),rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=52,title='HW6 LLMOps Pipeline - Draft Evidence Report',author='CMPE 297 Project Team').build(story,onFirstPage=page,onLaterPages=page)
print(args.output)

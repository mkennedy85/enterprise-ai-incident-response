# Enterprise AI Incident Response - CMPE 297 HW6

Minimal LLM incident investigator and release pipeline. Runtime and tests use Python 3.10+ standard library only. The only external request is to OpenAI's Responses API. No automatic mock fallback exists.

## Current completion status

Implemented: pinned model, prompt, evidence-only retrieval, structured report validation, versioned artifact hashes, 41 evaluation cases, real observed regression, unit/contract tests, PR CI, and runbook. The original starter SHIP/BLOCK exercise is recorded. No hosted-model baseline, live candidate verdict, GitHub PR or CI run exists yet: API credentials are pending. The public repository is https://github.com/mkennedy85/enterprise-ai-incident-response. The PDF is a draft until those results are added.

The old 100% deterministic results are archived under `evidence/legacy/`; they are NOT the LLM baseline. `baseline.json` intentionally does not exist until a successful live measurement.

## Quick local checks (no key or charges)

```sh
cd ~/Desktop/HW6_Enterprise_AI_Incident_Response
python3 -m unittest discover -s tests -v
python3 scripts/release.py --check
python3 eval_gate.py --hash
```

## One live investigation

Set `OPENAI_API_KEY` in the process environment, then:

```sh
python3 demo.py 'Investigate INC-001'
python3 demo.py 'Why did inventory-service restart during INC-004?' --json
```

`.env.example` documents the variable; the application does not auto-load .env files. Never paste keys into chat or commit them. A missing key yields an explicit error, not a simulated answer. Use `scripts/with_api_key.py` for a hidden interactive prompt when running locally.

## Real release comparison (after credentials are configured)

Local branches separate the pre-change release (`main`, legacy-keyword-v1) from the candidate (`hw6/diagnostic-guard-fix`, diagnostic-aware-v2). Both use the same 41-case evaluation including the regression. The candidate changes a setting, not expected answers. The baseline intentionally exposes the known false refusal.

1. Switch to `main`. Run one live demo to check access. Run `python3 scripts/live_measure.py aa`, which invokes `python3 eval_gate.py --aa` for ten runs and preserves the output. Review the scores and errors; commit `baseline.json` and `evidence/live/aa/` with the measured release. The application is not deployed, so this is a local pre-change reference release, not a claim of production operation.
2. Switch to `hw6/diagnostic-guard-fix`, merge `main` to inherit the exact baseline, and run `python3 scripts/live_measure.py gate`. It performs five fresh runs, using the unchanged committed baseline. A BLOCK is valid evidence; investigate it without weakening checks or replacing the baseline.
3. Push `main` and the candidate to the chosen GitHub repository; add the `OPENAI_API_KEY` Actions secret. Open a PR from the candidate to `main` and record the PR URL and CI run URL.
4. Download CI artifacts. Record the tested head commit, gate numbers, and URLs in `docs/submission_metadata.json`; generate the report. Every team member submits the same final PDF.

`live_measure.py` refuses to overwrite prior captured evidence; archive the old measurement folder explicitly if a failed setup must be retried. Each full A/A run makes up to 320 model calls on main; the candidate gate makes up to 165. A smoke call is additional. There are no automatic retries. max_output_tokens=1800, timeout=45 seconds per call, and sequential execution bound usage. A full run can take several minutes. Check account billing and model access before running.

## Project layout

- `incident_agent/`: real HTTP model client, read-only retrieval, guard, report validation.
- `data/incidents.json`: four synthetic incidents, with metric/trace/change/runbook records. No ground-truth hypotheses.
- `data/ground_truth.json`: labels for evaluation development only; never loaded by runtime.
- `prompts/`, `config/`, `manifest.json`: answer-changing artifacts with content hashes.
- `eval_set.jsonl`: 41 cases; evaluation hash 818ff18c5996.
- `eval_gate.py`: instructor gate with documented correctness fixes and evidence logging.
- `evidence/`: starter exercise, archived offline results, actual regression observation, local test results; live results will be added after credentials.
- `docs/`: runbook, release change, evaluation rationale, completion checklist and metadata.
- `reference/`: originals retained locally and excluded from Git publishing.

## Scope and evaluation limits

This is a single model call over exact incident retrieval, not multi-agent orchestration or semantic RAG. Four synthetic incidents are not a deployed microservice environment. Model cause-line checks allow a few phrasings but remain heuristic, and citation-ID validation proves referential validity, not semantic entailment. Safety filters and redaction are limited to this synthetic demonstration. No write tools are exposed. Real service connectors, a dashboard, independent incidents, and richer evidence scoring remain project work.

The gate uses characters/4 as its original answer-token proxy; actual API input/output token usage and latency are separately logged per case. No live cost or quality claim is made before measurement. `seed` is ignored because this Responses integration does not expose that parameter; independent live calls measure observed variability.

API contract and pinned model sources:
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/models/gpt-5.4-mini

## Run entirely through GitHub Actions

After adding the OPENAI_API_KEY repository secret, manually dispatch the **Measure HW6 baseline** workflow on main. It runs a smoke test and ten-run A/A, and uploads the baseline plus output without automatically committing it. Review and download that artifact, commit baseline.json and the captured evidence to main, merge main into the candidate, then open its PR to run the comparison. This route needs no local API-key file.

# Remaining steps requiring your account

1. Choose the GitHub owner/repository (connected account: mkennedy85), visibility, and whether an existing repo should be used. No remote was created or pushed.
2. Configure an OpenAI API key with billing and access to gpt-5.4-mini-2026-03-17. Enter it through scripts/with_api_key.py locally or set OPENAI_API_KEY in the environment; add the same variable name as a GitHub Actions repository secret. Do not paste the key into chat. The helper passes it to a child process without saving it.
3. On main, run one live smoke test, then capture ten-run A/A with scripts/live_measure.py aa. Review the real scores and commit baseline.json and evidence/live/aa/.
4. On hw6/diagnostic-guard-fix, merge main to inherit the baseline. Run scripts/live_measure.py gate, preserve the verdict, and publish the candidate PR. GitHub CI uses the base branch's baseline and five candidate runs. GitHub does not supply repository secrets to ordinary fork PRs; use a branch in your own repo for this trusted homework change. Do not switch to pull_request_target to run untrusted code with secrets.
5. Fill docs/submission_metadata.json with team members, repo URL, tested commit, PR URL, CI URL and on-call owner. Generate the final PDF with scripts/build_report.py using a Python environment containing reportlab, inspect it, then every teammate uploads the same PDF.

The current report is deliberately labeled DRAFT. Local mock tests, historical fixture scores, missing-key errors, and starter examples are distinguished from real model measurements. If the hosted run or CI fails, retain the error and describe what was tried; the assignment explicitly allows honest failure.

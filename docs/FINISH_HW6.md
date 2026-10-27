# HW6 completion status

Live baseline and candidate evaluation are complete. Team: Michael Kennedy and Alekya Gudise.

- Baseline: 10 runs, 41 cases per run, 76.3% mean check pass rate; range 73.2%-80.5%.
- Candidate: 5 runs, 41 cases per run, 80.5% mean; SHIP.
- Critical safety: 100% in both phases.
- Actual regression: 0/10 baseline passes, 5/5 candidate passes.
- Token proxy: +2.3%, below the 20% limit.

The report explains the word-order-sensitive scorer and distinguishes automated checks from diagnosis accuracy. Source results, response logs and provenance are committed under evidence/live/. No eval cases were changed after observing live results.

Repository: https://github.com/mkennedy85/enterprise-ai-incident-response
Pull request: https://github.com/mkennedy85/enterprise-ai-incident-response/pull/1
Baseline CI: https://github.com/mkennedy85/enterprise-ai-incident-response/actions/runs/40448294428
Candidate CI: https://github.com/mkennedy85/enterprise-ai-incident-response/actions/runs/40449785439

Remaining human step: review the final PDF and have both team members upload that same PDF to the assignment. Merging or deploying the candidate is separate from this submission.

# Evaluation design and gate rationale

41 cases: diagnosis 13, evidence 12, recommendation 4, hypotheses 4, abstention 4, safety 4. Safety is the only critical category (4/41): exposing credentials or executing requested changes must never ship. Every safety case must pass in every comparison run.

Diagnosis is checked on the model's `Likely cause:` line; quoting a correct evidence record elsewhere cannot satisfy it. Evidence checks require the expected evidence ID on that cause line as well as a plausible diagnosis. Recommendation and alternative checks combine a correct diagnosis with required report features. A human should review saved responses for semantic support: regex checks are not a complete factuality metric. Cases were authored before live model runs; no expectations have been weakened to make a model pass.

Gate rationale: max_drop_sigma=3 flags a decrease larger than three measured comparison standard deviations, while max_token_increase=0.20 permits modest answer-length variability but blocks a greater-than-20% increase in the starter's token proxy. These are engineering thresholds, not a statistical guarantee with only ten baseline runs. Gate runs=5, A/A runs=10. With zero sigma, any measured noncritical drop blocks; critical failures always block. Actual API usage is recorded separately.

For baseline and candidate, use the same post-regression eval hash 818ff18c5996. The pre-regression LLM eval hash is 9575fc6fb725. The archived original fixture eval hash 518edd13f8e1 belongs to a different system and is not comparable to the LLM results.

## Instructor gate changes

The original remains in local reference/HW6_starter/eval_gate.py. Changes made for correctness and auditability:

- Validate manifest content hashes before measurement.
- Reject a baseline/eval hash mismatch (the starter only warned).
- Reject incompatible baseline categories or comparison run counts.
- Abort on application/API errors; do not let an unavailable model become a zero-quality baseline that can later SHIP.
- Preserve per-case answers/errors, API usage and latency in eval_results.jsonl, plus per-category min/max spread in baseline.json.
- Remove stale report files at the beginning of a measurement and reject invalid run counts or empty evaluations.

Original category scoring, sigma calculation, critical-category behavior and answer-length gate remain intact. CI restores baseline.json from the PR base commit so a candidate cannot quietly replace it.

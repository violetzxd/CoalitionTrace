# CoalitionTrace pilot preregistration (2026-09-20)

## Primary scope

- Task: recover a smallest sufficient document set for an observed attacker target.
- Main paper scope: strict `r=2` bridge and trigger--payload coalitions only.
- Utility: normalized exact match to the frozen target answer under greedy decoding.
- Threshold: `tau=1`; no test-set tuning.
- Context intervention: fixed slot and order; absent documents are replaced by
  pre-generated neutral, length-controlled passages.
- Oracle subset: all `2^n` masks for `n<=12`; all minimum sufficient masks are saved.

## Primary metrics and go/no-go rules

- Exact coalition match (correct if any oracle minimum is returned), member F1,
  verified 1-minimal validity, false-coalition rate, replay count and token count.
- Go: ECM >= .70, member F1 >= .85, validity >= .95, false coalition <= .05.
- Improvement over the strongest equal-budget baseline: >= .10 ECM absolute with
  query-level paired-bootstrap 95% CI excluding zero.
- Oracle subset: >= .90 global-minimum correctness using <=25% of exhaustive calls.
- If two strict families cannot be generated automatically, or improvement over
  KernelSHAP/ddmin is below 8--10 points, report a no-go and do not submit inflated
  claims.

## Fairness and leakage controls

- Every generator call, including ranking-to-set conversion and final validation,
  is charged to the method budget.
- Structural features never expose poison roles, target answers, or oracle labels.
- Generation templates/entities/seeds are split before evaluation.
- Query is the statistical unit.  Paired bootstrap and McNemar tests use query IDs.
- Results distinguish conditional-on-co-retrieval attribution from end-to-end RAG.

## Required robustness before a paper claim

- deletion, neutral length-matched, and clean/prior-version replacements;
- at least two prompt orders and three paired seeds;
- Qwen2.5-7B-Instruct and Mistral-7B-Instruct-v0.3;
- clean, redundant multi-poison, and hard-negative controls.


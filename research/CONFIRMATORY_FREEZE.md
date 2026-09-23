# Confirmatory freeze — 2026-09-20

This file separates development decisions from held-out evaluation.

## Data split and sampling unit

- Development used only the first 14 rows labeled `dev` from the existing public
  PoisonedRAG-derived HotpotQA/NQ assets.
- Confirmatory evaluation uses only rows already labeled `test` by the pinned
  pre-model split seed. HotpotQA and NQ each contain 70 test source queries.
- A source query is the statistical unit. Multiple construction candidates for a
  source are a screening funnel, not independent samples.
- For each dataset/model/stratum, select the first candidate in fixed generation
  order satisfying the oracle stratum definition. Selection cannot use any method
  output. Report source-level yield and all rejected candidates.

## Frozen candidate order per source

1. U-size2; 2. U-size3; 3--4. two A-size2-disjoint position/code variants;
5. A-size2-overlap; 6. A-size3-disjoint; 7. A-size3-overlap; 8. explicit N.

U/A selection requires `v(empty)=0`, `v(D)=1`, exact full-table monotonicity and
the required count of inclusion-minimal causes. N requires the endpoint conditions
and a Boolean cover-edge violation; stable-N is assigned only after robustness
audits. Candidate planting is never used as ground truth.

## Method and primary comparison

- Method: LOO backbone fast path plus cached exclusion tree and balanced chunk
  minimization, with conditional completeness under monotonicity.
- Primary small-n budget: 48 unique mask replays.
- Primary A endpoint: all-cause exact match (ACEM) against the strongest equal-
  budget baseline.
- Frozen gate: A ACEM >= .70, improvement >= .10, query-level paired-bootstrap
  95% CI excluding zero; U ACEM >= .95 and within 2 points of LOO; verified cause
  validity >= .95; unsafe unconditional completeness = 0.
- Development tables and all R1--R4 revisions are excluded from confirmatory
  confidence intervals.

## Analysis

McNemar exact test for paired ACEM; source-query paired bootstrap with 10,000
resamples for ACEM/cause-F1/call differences; Holm correction over the declared
baseline family. Report dataset/model cells separately before any pooled summary.

No threshold, budget, template order or baseline setting may change after reading
confirmatory method results. A failed cell is reported as a failure.

## Predeclared construction-family robustness

Before reading confirmatory outputs, a second `news` wording family was frozen.
It replaces registry language with report/appendix language while preserving the
same causal graph. It is evaluated as a descriptive held-out construction-family
robustness check and is not used to change the primary budget or method.

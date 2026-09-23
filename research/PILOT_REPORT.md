# CoalitionTrace pilot report

Date: 2026-09-20. Status: **no-go for the original ICASSP claim** pending the
second-model audit.

## Frozen execution

- GPU server: `bear`; Qwen run on one H100 80 GB, Mistral run on one A800 80 GB.
- Models: locally cached frozen Qwen2.5-7B-Instruct and
  Mistral-7B-Instruct-v0.3 checkpoints recorded by the server asset lock.
- Decoding: greedy, at most 16 generated tokens.
- Cases: HotpotQA queries from the pre-existing public pilot pool; two generated
  document families (`bridge`, `trigger_payload`), six clean/distractor slots, and
  a neutral replacement for every slot.
- Screening evaluates the clean-background mask, each poison singleton, and the
  pair.  Complete oracle evaluation replays all `2^8=256` masks and records every
  minimum sufficient set.

## Generation audit

- 200 automatically generated candidates (100 per family) were screened on each
  model; 77 were strict under the four-mask screen for Qwen and 77 for Mistral.
- 44 cases were strict on both models (22 per family).  This is an automatic
  acceptance rate of 22% jointly, with no manual answer selection.
- Forty Qwen-screened cases (20 per family) received complete all-mask replay.
  In 32/40, the intended two-document poison pair was one of the global minimum
  sufficient sets.  The eight rejected cases included singleton alternatives and
  minima of sizes 2--6, showing why poison-only subset checks are insufficient.

## Attribution results on the 32 full-oracle pair cases

All calls used by ranking, candidate selection, sufficiency, and necessity checks
are charged to the same budget.

| Method | ECM @16 | ECM @32 |
|---|---:|---:|
| CoalitionTrace pairwise active surrogate | 0.6875 | 0.8750 |
| Linear active surrogate | 0.0000 | 0.9062 |
| Random pair search | 0.0312 | **1.0000** |
| Greedy deletion | 0.0312 | 0.9062 |
| LOO ranking + real validation | **0.6875** | 0.6875 |
| KernelSHAP + real validation | 0.0938 | 0.9062 |

At budget 16, CoalitionTrace ties rather than exceeds LOO.  At budget 32 it loses
to random search, greedy deletion, KernelSHAP, and even the linear ablation.  It
therefore fails the preregistered requirement of an absolute 10-point improvement
over the strongest equal-budget baseline.

## Scientific interpretation

The negative result is structural, not merely an implementation miss.  If the
observed full context is sufficient and every member of a proposed pair is
necessary relative to that context, a binary LOO replay directly observes a large
marginal change for each member.  Thus a benchmark built around strict member
necessity can make LOO unusually strong; the motivating claim that LOO must miss
such pairs is not generally valid.  At `n=8`, budget 32 also nearly enumerates all
28 pairs, so random pair search is an exact and cheap baseline.

## Decision

Do not submit the current result as a positive ICASSP paper.  A defensible pivot
must change the regime rather than selectively report budgets:

1. `n >> B` pair localization with a non-label-derived structural candidate graph;
2. contexts with multiple redundant sufficient coalitions, where grand-coalition
   LOO is provably uninformative, while scoring any oracle minimum as correct; or
3. a benchmark/analysis paper demonstrating the contradiction between common
   synergy narratives and member-necessity evaluation.

Any pivot still requires a second dataset, the second generator, non-template
controls, fair official baselines, and at least 100 independent strict test cases
per primary cell.  These are not yet complete.

## Corrected v3 audit (position randomized; standards-compliant baselines)

After the independent review found fixed-slot leakage, all slots were permuted by
a case-derived hash and every algorithm seed was derived independently from the
case ID.  KernelSHAP was replaced by Shapley-kernel weighted regression with
endpoint constraints; complement-based delta debugging was separated from greedy
deletion; member F1 now takes the best match over all valid oracle minima.

Of 40 newly replayed Qwen cases, the intended pair was a global minimum in 26.
Complete-table analysis classified 10/40 as monotone with one inclusion-minimal
cause and 30/40 as non-monotone; there were no monotone alternative-cause cases.
The LOO-backbone theorem had zero violations on the monotone cases.

| Method | ECM @16 | ECM @32 | mean queries @16 | mean queries @32 |
|---|---:|---:|---:|---:|
| CoalitionTrace | 0.6538 | 1.0000 | 16.00 | 21.35 |
| Linear ablation | 0.2692 | 1.0000 | 16.00 | 22.58 |
| Random pair search | 0.4615 | 0.8846 | 12.50 | 18.46 |
| Greedy deletion | 0.6538 | 1.0000 | 14.35 | 15.04 |
| **Hierarchical deletion** | **1.0000** | **1.0000** | **11.35** | **11.35** |
| LOO + validation | 0.7692 | 0.7692 | 12.92 | 16.62 |
| KernelSHAP + validation | 0.1923 | 0.3846 | 14.89 | 29.62 |

The corrected result strengthens the no-go: complement-based hierarchical deletion achieves perfect exact
recovery with roughly half the queries used by CoalitionTrace.  The original
method is therefore not merely below its go threshold; it is dominated on its own
primary benchmark.

The independently replayed Mistral v3 audit reproduced the conclusion.  Of 36
full-oracle cases, 26 retained the intended pair as a global minimum; 9/36 were
monotone unique-cause cases and 27/36 were non-monotone, again with zero theorem
violations.  On the 26 intended-pair cases, CoalitionTrace obtained ECM .6538 at
budget 16 and .9615 at budget 32.  Hierarchical deletion obtained 1.0 at both budgets
with 10.31 mean queries; LOO obtained .8462.  The no-go therefore transfers across
both frozen 7B generators.

# Independent review of the ambiguity-aware pivot protocol

Date: 2026-09-20  
Role: independent ICASSP 2027 reviewer  
Decision on protocol: **promising but not frozen until the mandatory revisions below are adopted**

## 1. Review summary

The pivot is scientifically justified by the corrected negative result: on both
Qwen2.5-7B-Instruct and Mistral-7B-Instruct-v0.3, complement-based minimization
dominates the original CoalitionTrace surrogate.  The two propositions in
`LOO_BOUNDARY_THEOREM.md` are correct for a Boolean monotone utility.  They support
a narrower question: when is grand-coalition leave-one-out sufficient, and when
must a forensic method search for alternative minimal causes?

The present protocol nevertheless mixes three distinct claims:

1. an oracle taxonomy of set functions (`U/A/N`);
2. a deployable algorithm that does not know the taxonomy;
3. a completeness certificate that is valid only under monotonicity.

These must be separated.  A method cannot infer global monotonicity from a small
number of replays.  In particular, failure to observe a monotonicity violation is
not evidence that none exists.  The paper may return a **monotonicity-conditional
completeness certificate**, but must not return an unconditional unique-cause or
all-causes certificate unless the full table has been evaluated.

The proposed exclusion-guided enumeration is sound and complete for monotone
Boolean utilities when allowed to exhaust its search tree.  It is not sound as a
complete enumerator for a non-monotone utility because an insufficient maximal
allowed set can contain a sufficient subset.  On detecting a violation, the
method must either abstain from completeness claims or switch to a general search
that makes no monotone pruning assumption.

## 2. Frozen problem definition

For one fixed query, ordered context, model revision, prompt, decoding rule and
counterfactual replacement policy, let `D={1,...,n}` and let

`v(S) = 1[target answer is produced under intervention S]`.

The primary paper should use deterministic greedy decoding, normalized exact
match and a frozen replacement policy so that every mask has an exact Boolean
value.  This defines a local replay function; it does not claim invariance across
models, prompt orders or replacement policies.  A probabilistic or semantic
utility may be a robustness analysis, but must not silently change the primary
ground truth.

Require `v(empty)=0` and `v(D)=1` for all primary cases.  Cases violating either
condition are reported as out-of-scope screening outcomes, not silently removed.

Define the complete set of inclusion-minimal sufficient causes as

`M(v) = {S subseteq D: v(S)=1 and v(T)=0 for every proper T subset S}`.

The primary target is `M(v)`, not the intended poison documents and not merely
the minimum-cardinality sufficient masks.  Intended poison membership is useful
only for construction-yield reporting.

For arbitrary non-monotone `v`, checking only immediate one-document deletions
establishes 1-minimality, not inclusion-minimality.  Exact validation of a
returned cause `S` in stratum `N` requires querying every proper subset of `S`
(feasible only for small causes) or labeling it explicitly as `1-minimal`.

## 3. Strict U/A/N taxonomy

Monotonicity is defined on the thresholded Boolean table:

`v(S) <= v(T)` for every `S subset T`.

With a complete table it is sufficient to check all cover edges
`v(S) <= v(S union {i})`.  The strata are:

- **U (unique monotone cause):** `v(empty)=0`, `v(D)=1`, `v` is monotone, and
  `|M(v)|=1`.
- **A (alternative monotone causes):** `v(empty)=0`, `v(D)=1`, `v` is monotone,
  and `|M(v)|>=2`.
- **N (non-monotone):** `v(empty)=0`, `v(D)=1`, and at least one cover edge has
  `v(S)=1` and `v(S union {i})=0`.

For `A`, report cause count, cause-size distribution, pairwise cause overlap and
backbone size `|intersection M(v)|`.  At least two difficulty bands are required:

- `A-disjoint/weak-overlap`: empty backbone or mean pairwise Jaccard at most .25;
- `A-overlap`: nonempty backbone and mean pairwise Jaccard above .25.

For `N`, report the number and proportion of violating cover edges, the minimum
and median layer at which violations occur, and whether a violation lies on a
search path taken by each method.  A single violating edge must not be presented
as a robust non-monotone phenomenon without further audit.

`U/A/N` are oracle analysis labels.  They must never be passed to the evaluated
algorithm or used to choose its budget, seed or branch policy.

## 4. Ground truth and pseudo-non-monotonicity controls

### 4.1 Exact oracle core

All primary accuracy claims require complete `2^n` tables.  Save every mask,
raw answer, normalized answer, target score, input/output token count, model
revision, prompt hash, replacement-policy hash and decoding configuration.

Compute `M(v)` from the full table.  Independently recompute monotonicity and
minimal causes with a second implementation on a random 10% audit sample.  Add
unit tests for empty, unique-cause, alternative-cause and non-monotone functions.

### 4.2 Intervention sensitivity

The current matched replacements can manufacture apparent non-monotonicity:
turning a slot on replaces one benign passage with another passage, and the
change may alter content, attention or truncation.  Therefore every `N` claim
must be audited under:

1. length-matched neutral replacement;
2. deletion plus fixed inert padding that preserves token budget and later-slot
   positions; and
3. a clean/prior-version replacement where available.

Report a base-policy `N` label and a `stable-N` label.  `stable-N` requires at
least one semantically corresponding violation to persist under two replacement
policies and two prompt orders.  The primary non-monotone result must be reported
both on all `N` and on `stable-N`.

Exact match is also fragile to formatting.  Store target-token log probability
or a calibrated target-vs-correct margin when the open model permits it.  A
violation supported only by exact-match formatting, but not by the margin, is a
measurement-sensitive violation and must be counted separately.

The deterministic table is the primary ground truth.  On at least 50 cases per
stratum and generator, repeat every mask needed to support the reported cause or
violation at three paired sampling seeds (`temperature=0.7`).  This is a
stability audit, not a redefinition of the frozen deterministic labels.

### 4.3 Selection accounting

Publish the complete funnel:

`generated -> clean-valid -> full-context attacked -> screened strict -> U/A/N -> final test`.

Slot position is independently permuted per case.  Template, entity, source
query and construction seed are split before screening.  The held-out test set
is frozen before method development.  No method may read `poison_indices`, the
intended family label, target-bearing template tags or oracle stratum.

## 5. Reviewed algorithm

### 5.1 LOO fast path

Query `v(D)`, all `v(D\{i})`, and form the LOO backbone

`B = {i: v(D\{i})=0}`.

Query `v(B)`.  If `v(B)=1`, the method may return `B` as the unique cause **under
the monotonicity assumption**.  It must attach status
`conditional-complete-if-monotone`; it may not claim to have empirically proved
global monotonicity.  If an observed cached pair violates monotonicity, this fast
path is disabled.

If `v(B)=0`, the monotone interpretation is that alternative causes exist and
the backbone alone is insufficient.  This is a trigger for enumeration, not a
proof that the function is monotone or belongs to `A`.

### 5.2 Cached exclusion-guided enumeration

For a monotone utility, the following search is acceptable:

1. Maintain a queue of exclusion sets `E`, initially `{empty}`, and a cache of
   every queried mask.
2. For a node `E`, query the maximal allowed set `D\E`.
3. If it is insufficient, prune the node only under the monotonicity assumption.
4. If it is sufficient, minimize it using cached complement/deletion queries to
   an inclusion-minimal cause `C`.
5. Record `C`.  For every `i in C`, enqueue the deduplicated child `E union {i}`.
6. Exhaustion of the queue gives an all-causes completeness certificate only
   conditional on monotonicity.  Budget exhaustion returns verified partial
   causes plus `incomplete-budget`, never a complete set claim.

This search is closely related to hitting-set trees, minimal-explanation
enumeration, monotone Boolean dualization and MUS/MCS enumeration.  The paper
must cite and compare with those literatures.  The enumeration tree itself
should not be claimed as a fundamentally new algorithm.  Potential novelty is
the RAG causal formulation, the LOO boundary, cache/budget adaptation and the
empirical ambiguity study.

The minimizer must have a precise contract.  Under monotonicity, repeated
single-deletion minimization is sufficient for inclusion-minimality.  The current
`ddmin` implementation tests complements but not the chunks themselves and
should be named `complement-based hierarchical deletion`, not canonical Zeller
`ddmin`, unless completed accordingly.

### 5.3 Non-monotone handling

Whenever cached observations contain `S subset T` with `v(S)=1` and `v(T)=0`,
monotone pruning and completeness claims stop immediately.  Pre-register one of
two primary policies:

- **Abstention policy (recommended for the four-page paper):** return all causes
  already exactly verified, status `abstain-observed-nonmonotone`, and no
  completeness claim.
- **General-search policy:** switch to size-ordered subset search with no
  monotone pruning.  At small `n`, this can be exact but may be exponential.

Do not present “no observed violation” as proof of monotonicity.  In blind
end-to-end evaluation, an `N` case on which the method emits a complete/unique
unconditional certificate is an unsafe certificate and counts as an error.

For ICASSP, abstention is the cleaner primary policy.  General search can be a
small-`n` oracle comparison or artifact feature.

## 6. Primary endpoints

All metrics use the query as the independent unit.

### Accuracy and coverage

- **All-Cause Exact Match (ACEM):** predicted set of sets equals `M(v)`.
- **Cause precision/recall/F1:** exact set-level matching between predicted and
  oracle causes; no member-overlap substitution in the primary metric.
- **Any-Cause Success:** at least one returned cause belongs to `M(v)`.
- **Verified-cause validity:** fraction of returned sets that are truly in
  `M(v)`; for `N`, distinguish exact inclusion-minimal from 1-minimal.
- **Backbone F1:** predicted LOO backbone versus `intersection M(v)`, reported
  only on monotone cases.

### Safety and efficiency

- **Unsafe completeness rate:** complete/unique claim when returned causes do not
  equal `M(v)`, or an unconditional claim without a valid assumption.
- **N detection recall and false alarm rate:** based only on violations observed
  by the algorithm, not oracle routing.
- **Selective risk/coverage:** cause error among non-abstained cases versus
  coverage, especially on `N`.
- Unique generator calls, input/output tokens, wall time and peak memory.
- Calls to first valid cause and calls to complete enumeration.

Report metrics separately for `U`, `A-disjoint`, `A-overlap`, all `N`, and
`stable-N`.  A pooled score without strata is not acceptable.

## 7. Statistical plan and frozen success criteria

The primary comparison is the proposed LOO-plus-enumerator versus the strongest
equal-budget baseline on `A`; the primary outcome is ACEM at a frozen budget.

- Compare paired binary outcomes with McNemar's exact test.
- Report paired query-level bootstrap (10,000 resamples) 95% confidence intervals
  for ACEM difference, cause-F1 difference and call-count difference.
- Use Holm correction across the pre-declared baseline family for the single
  primary budget.  Other budgets form a descriptive accuracy-budget curve.
- Report absolute differences and matched odds ratios; do not rely only on
  p-values.
- Perform power analysis from a disjoint pilot.  The target practical difference
  remains at least +10 percentage points ACEM over the strongest equal-budget
  baseline.

Frozen go criteria:

- `U`: ACEM at least .95, no lower than LOO by more than 2 points, and no more
  than two additional validation calls beyond the declared fast path.
- `A`: ACEM at least .70 and at least +.10 over the strongest equal-budget
  baseline, with paired-bootstrap 95% CI excluding zero.
- All returned causes: exact verified validity at least .95 and false-cause rate
  at most .05.
- Unsafe completeness rate must be zero on the complete-oracle core.
- `N`: abstention/detection recall at least .80 at false alarm rate at most .10;
  report selective cause risk rather than forcing an answer.
- The direction must hold on both generators and both datasets.  Failure on one
  is reported; it may not be hidden by pooling.

## 8. Mandatory baselines and ablations

Baselines must receive identical replay budgets, including validation:

1. LOO backbone plus direct validation;
2. greedy deletion with at least ten case-derived deletion orders;
3. canonical ddmin if implemented, and the current complement-based hierarchical
   deletion under its accurate name;
4. a standard hitting-set/minimal-explanation enumerator with the same cache;
5. random balanced group probes plus the same minimizer/validator;
6. correctly weighted KernelSHAP and ContextCite-style mask regression, converted
   to causes with all conversion queries charged;
7. exhaustive oracle for small `n` only.

Required ablations are: no LOO fast path, no query cache, no exclusion guidance,
random exclusion order, and forced monotone search on `N` to quantify unsafe
certificates.  If the proposed enumerator is algorithmically identical to the
standard hitting-set baseline after caching, it must be presented as an
application/adaptation, not a new search algorithm.

## 9. Minimum publishable experiment matrix

The following is the smallest matrix I would regard as credible for an ICASSP
regular paper; fewer cells should be treated as a pilot:

### Fully oracled RAG core

- datasets: HotpotQA and Natural Questions;
- generators: frozen Qwen2.5-7B-Instruct and Mistral-7B-Instruct-v0.3;
- context size: `n=8` for all cases, plus an `n=10` oracle subset;
- strata: at least 100 independent `U`, 100 `A` and 100 `N` test queries per
  generator after pooling the two datasets, with each dataset contributing at
  least 40 cases to every stratum;
- `A`: at least 40 weak-overlap/disjoint and 40 overlap cases per generator;
- `n=10`: at least 30 `A` cases per dataset-generator cell, fully enumerated;
- cause sizes: 2 and 3, with neither below 25% of `A`;
- complete `2^n` replay tables for every primary case.

The same source query may be evaluated by both generators, but it counts once in
cross-model pooled statistical analyses.  Generator-specific results remain
paired diagnostic replications.

### Robustness

- two prompt orders and the three replacement policies described above;
- three paired stochastic decoding seeds on the audited subset;
- at least one held-out construction family not seen during method development;
- clean, redundant-poison and hard-negative controls for false-cause behavior.

### Scalability

Use `n=16` and `n=32` only for query-cost curves.  Unless all subsets are
enumerated, do not report ACEM or all-cause recall as exact ground-truth metrics.
Planted monotone Boolean simulations may establish scaling, but must be clearly
separated from LLM evidence.  On large RAG contexts report verified-cause
validity, time to first cause and conditional completeness status.

This matrix is substantial.  If the submission deadline prevents its completion,
the correct outcome is to defer submission, not to relax the strata or oracle
requirements after observing results.

## 10. Reproducibility and paper claims

- Freeze Python (at least 3.10), CUDA, Transformers, model revisions and all
  hashes in a machine-readable lock.  The current local Python 3.9 environment
  cannot run `int.bit_count` despite the declared `python>=3.10` requirement.
- Add independent tests for the theorem identities, inclusion-minima enumeration,
  cache accounting, budget exhaustion and non-monotone abstention.
- Record every rejected/generated case so acceptance rates are auditable.
- Disclose AI-assisted poison generation and manuscript/code generation under
  the ICASSP/IEEE policy.
- Limit the central claim to the fixed replay intervention.  Do not equate a
  minimal sufficient document set with real-world attacker identity.

Recommended paper claim if the gates are met:

> Grand-coalition LOO exactly identifies the common backbone of monotone minimal
> causes and solves the unique-cause case.  An assumption-explicit,
> exclusion-guided enumerator recovers alternative causes under a replay budget,
> while conservative abstention prevents unsupported completeness claims when
> non-monotonicity is observed.

Claims that LOO generally fails, that the method certifies monotonicity from
limited queries, or that exclusion-guided enumeration is wholly novel would not
survive review.

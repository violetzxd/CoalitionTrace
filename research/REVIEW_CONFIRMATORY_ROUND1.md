# Independent review of confirmatory round 1

Date: 2026-09-20  
Standard: ICASSP regular paper, realistic CCF-B / approximately 40% acceptance  
Scope: read-only review; no algorithm changes

## 1. Verdict

The two Qwen cells provide credible confirmatory evidence for one narrow claim:

> Conditional on a monotone Boolean replay utility with multiple
> inclusion-minimal causes, cached exclusion-guided enumeration recovers the full
> cause set more often than repeated random-order deletion at budget 48.

The evidence is not yet sufficient for a method-centered positive paper.  The
defensible current paper shape is **theory/benchmark plus a positive monotone-A
result and an explicit negative-N boundary**.  A strictly monotone positive paper
could become defensible only after the accounting correction, a second generator,
a held-out construction family, a standard explanation-enumeration baseline and
the remaining frozen matrix all replicate the result.

The non-monotone claim has failed.  AmbiCause detects only .511 of NQ `N` and
.552 of HotpotQA `N`; the post-development upward audit reaches .707 on HotpotQA,
still below the frozen .80 gate.  The audit is a new exploratory method and must
not replace the original confirmatory result.  The paper must not claim that the
algorithm reliably determines when its monotonicity assumption is violated.

## 2. What the current results establish

At the source-query level:

- NQ `A`: AmbiCause ACEM is .959 (47/49) versus .816 (40/49) for the
  preselected seed-0 RepeatedGreedy comparison, an absolute difference of .143;
  bootstrap 95% CI [.041, .265], McNemar exact p=.039.
- HotpotQA `A`: AmbiCause ACEM is 1.000 (58/58) versus .862 (50/58), an
  absolute difference of .138; bootstrap 95% CI [.052, .224], McNemar exact
  p=.0078.
- The ten-seed RepeatedGreedy means (.757 and .795) are lower, so seed 0 is not a
  favorable baseline choice for AmbiCause.  This reduces, but does not remove,
  the need for a predeclared stochastic-baseline analysis.
- On `U`, AmbiCause and LOO both obtain ACEM 1.0.  This supports the theorem's
  fast-path consequence.  The relevant efficiency comparator on `U` is LOO, not
  RepeatedGreedy; no claim should be made that AmbiCause improves on LOO there.

Both `A` cells exceed the frozen +.10 practical-difference gate and their paired
bootstrap intervals exclude zero.  These are real positive results, not a pooled
rescue of a failed cell.  However, they cover one generator, one template family,
`n=8`, and predominantly the first successful construction in a fixed candidate
order.  They establish internal validity for this benchmark slice, not broad RAG
forensic validity.

## 3. Statistical audit

### 3.1 Unit and pairing

The source query is correctly used as the unit.  Each source contributes at most
one selected case to a given dataset/model/stratum.  Masks, causes and algorithm
seeds must never be counted as additional independent observations.

If results are pooled across datasets, resampling must be stratified by dataset.
If the same source is evaluated under two generators, it still counts once in a
cross-model pooled analysis; model is a repeated condition.

### 3.2 Stochastic baselines

The primary comparison currently uses one global RepeatedGreedy seed while also
reporting a ten-seed mean.  The final paper should predeclare one of these two
analyses and retain the other as sensitivity:

1. derive one baseline seed independently from each case ID and compare paired
   binary ACEM; or
2. average each source's outcome over the ten frozen seeds, then perform the
   source-level paired bootstrap on those per-source expectations.

Do not treat the ten seeds as ten observations.  Report the distribution across
seeds and the probability that AmbiCause beats the baseline, not only the grand
mean.  Because seed 0 is stronger than the ten-seed mean here, the current effect
is conservative, but the analysis rule still must be made consistent.

### 3.3 Multiplicity

The reported McNemar p-values are unadjusted.  `CONFIRMATORY_FREEZE.md` requires
Holm correction over the declared baseline family.  Report every predeclared
comparison and its adjusted p-value.  If only the two dataset tests against a
single predeclared primary baseline form the confirmatory family, both results
remain below .05 after Holm.  If LOO, hierarchical deletion, KernelSHAP, random
masks and repeated deletion are all confirmatory hypotheses, NQ p=.039 may not
survive correction.  This does not invalidate the effect-size confidence
interval, but it changes the significance wording.

The manuscript should lead with absolute effect and paired confidence interval,
not “significant on both datasets,” until the correction family is resolved.

### 3.4 Sample-size deviation

The approved pivot protocol stated at least 100 test queries per
dataset/model/stratum.  The later freeze contains only 70 test sources per
dataset and yields 49/49/45 and 56/58/58.  The pooled Qwen totals exceed 100 per
stratum and each dataset contributes more than 40, matching the independent
review's minimum matrix, but not the literal investigator-approved protocol.

This must be recorded as a feasibility deviation.  Either collect an independent
extension cohort to reach the original per-cell target, or state that the study
uses the pooled-per-generator rule and keep dataset-specific intervals.  The rule
cannot be silently rewritten after seeing results.

## 4. Baseline and budget fairness

### 4.1 Prompt-equivalence caching is a blocking issue

In the confirmatory construction, noncausal slots are identical in `observed`
and `replacement`.  Consequently, many different masks produce byte-identical
prompts.  The oracle collector may evaluate an identical prompt once and copy its
value, but the online methods cache and charge by mask, not by prompt hash.

This creates two incompatible interpretations:

- If the metric is **actual generator replays**, byte-identical prompts must be
  canonicalized and cached for every method.  RepeatedGreedy is likely charged
  many calls that are free under such a cache, so the reported 12 versus 46--47
  call advantage is not yet valid.
- If the metric is **abstract mask queries**, every mask may be charged, but the
  paper must not call the count generator calls or token cost, and copied oracle
  generations must be counted consistently as logical queries.

The preferred correction is a shared prompt-hash oracle cache with budgets based
on unique rendered prompts.  Re-run every method on the existing frozen tables
using this common accounting, without changing method decisions.  Report both
unique masks and unique prompt hashes.  If the ACEM advantage disappears at an
equal actual-call budget, the positive method claim fails.

The effective dimension must also be disclosed.  An `n=8` table with four fixed
noncausal slots may have only four causally variable prompt dimensions.  Report
the number of unique rendered prompts per case and do not present `2^8` as 256
distinct LLM interventions when many are duplicates.

### 4.2 Required algorithmic baselines

RepeatedGreedy is a relevant heuristic but is not sufficient as the sole strong
enumeration baseline.  The exclusion tree is closely related to established
hitting-set and minimal-explanation enumeration.  A positive paper requires:

1. LOO backbone plus validation;
2. repeated deletion with ten frozen case-derived seeds;
3. complement-based hierarchical deletion under that accurate name;
4. a standard hitting-set/minimal-explanation enumerator using the same
   minimizer and prompt cache;
5. random balanced group/mask enumeration;
6. correctly weighted KernelSHAP or ContextCite-style mask regression with every
   set-conversion and validation query charged;
7. exhaustive oracle at `n=8/10`.

The paper cannot claim a new exclusion-enumeration algorithm if the standard
hitting-set baseline is equivalent after caching.  In that event, present
AmbiCause as an assumption-explicit RAG adaptation and make the benchmark/boundary
analysis the primary contribution.

### 4.3 Budget selection

Budget 48 was chosen after a two-case development A set.  It was frozen before
the held-out cells, so the confirmatory test is not invalid, but the development
sample is too small to establish a generally meaningful operating point.  Keep
48 as the single confirmatory budget and show 16/24/32/48/64 curves as descriptive
robustness without selecting a new “best” point.

## 5. Template and construction threats

### 5.1 Repeated causal graph

The registry family repeatedly instantiates the same question-routing and
record-payload graph.  Method inputs do not expose planted labels, so this is not
direct feature leakage, but it produces a narrow distribution of monotone Boolean
functions.  Since selection takes the first candidate realizing `A`, successful
cases may be dominated by size-2 disjoint causes, the easiest exclusion pattern.

Before a positive claim, report for each cell:

- realized number of causes `|M(v)|`;
- cause-size histogram;
- disjoint versus overlapping causes and backbone size;
- planted-to-realized cause correspondence;
- cross-path recombination causes;
- ACEM and calls within each difficulty band.

At least 25% of A cases should contain size-3 causes, and both weak-overlap and
overlap strata need enough cases for separate intervals.  If the present frozen
set lacks these, collect a separately labeled extension rather than resampling
the successful easy templates.

### 5.2 Held-out family

The frozen `news` family changes wording but preserves almost the same causal
graph.  It is a useful first robustness check, not a strong out-of-family test.
It must be run because it was frozen before confirmatory output.  In addition,
include at least one structurally distinct ambiguity family, such as independent
multi-hop evidence paths or independently worded corroboration routes without a
shared registry/report identifier.

Template instances, source queries, answers and target entities must not cross
development/test families.  Report exact-prompt hash multiplicities both within
a case and across cases.  Any duplicate prompt across source queries must be
deduplicated or clustered at the source level.

### 5.3 Screening interpretation

The U/A/N yields are construction yields, not estimates of how frequently U, A
or N occurs naturally in deployed RAG.  A source may yield one selected case in
each stratum because multiple planted candidates were screened.  The paper must
not say that, for example, “most real RAG failures are non-monotone” from these
counts.

## 6. Non-monotone result and framing

The original AmbiCause N result fails its preregistered gate by a large margin.
The method often does not encounter a monotonicity-violating edge within budget,
so the absence of an observed violation cannot safely activate an unconditional
certificate.  This is the expected identifiability problem, not a cosmetic
implementation issue.

The upward audit was developed after the first held-out result and remains below
the .80 gate.  It may appear as an explicitly exploratory ablation.  It must not
be merged into AmbiCause, used to replace the frozen N result or described as
confirmatory.

For the final paper:

- all complete/unique statements remain conditional on monotonicity;
- N is reported as a negative stress test;
- no claim is made that the system reliably recognizes whether monotonicity
  holds;
- general deployment guidance is “use only when monotonicity is externally
  justified or accept conditional outputs,” not “the method automatically knows
  when to abstain.”

To support a `stable-N` benchmark contribution, complete the frozen continuous
margin, second replacement-policy and second prompt-order audits.  Report the
number of raw-N cases remaining stable and detection separately on raw-N and
stable-N.  Do not tune the tolerance on the confirmatory cells.

## 7. Required remaining experiments

The minimum additions before submission are:

1. Correct prompt-hash accounting and rerun all Qwen comparisons at equal actual
   replay budgets.
2. Complete both NQ and HotpotQA on the frozen Mistral model with no method or
   threshold changes.
3. Run the frozen news-family test; add a structurally distinct held-out family
   if claiming more than template-level generalization.
4. Add the standard hitting-set/minimal-explanation enumerator and all declared
   equal-budget baselines, then apply the frozen Holm correction.
5. Report ten-seed stochastic-baseline results with source-level uncertainty.
6. Provide A difficulty breakdowns (`|M|`, size, overlap, backbone and
   recombination) and a fully oracled `n=10` A subset.
7. Complete margin/order/replacement audits and identify `stable-N`.
8. Add clean and hard-negative controls for false-cause behavior.
9. Report dataset-specific screening funnels, prompt-hash multiplicity, actual
   tokens, wall time and model/runtime hashes.

ICASSP has only four technical pages.  If all additions cannot fit, keep the
primary story to theorem + U/A benchmark + A enumeration, and use N as one compact
failure/limitation table with the full audit in the artifact.  Do not omit the N
failure from the paper.

## 8. Acceptance threshold for the next review

A conditionally positive monotone-ambiguity paper becomes defensible if all of
the following hold after prompt-equivalent caching:

- both datasets and both generators retain A ACEM at least .70;
- improvement over the strongest fair equal-budget enumerator is at least .10 in
  every primary cell, with dataset-specific paired intervals excluding zero or a
  predeclared stratified combined analysis plus no contradictory cell;
- U remains tied with LOO and does not add material replay cost;
- verified cause validity is at least .95 and unsafe unconditional completeness
  is zero;
- a held-out family and the `n=10` subset preserve the qualitative advantage;
- Holm-adjusted inference and the source-level multi-seed analysis are reported;
- N failure is explicitly scoped out rather than repaired post hoc.

If the advantage vanishes against prompt-cached hitting-set/repeated-deletion
baselines, the work should be submitted only as a benchmark/theory/negative-N
paper, or deferred.  Given the current evidence, my score is:

- theory/benchmark + positive-A + negative-N framing: **5/10, borderline**, with
  a path to weak accept after the mandatory additions;
- general-purpose AmbiCause method paper: **3/10, reject**;
- strictly monotone method paper today, before the missing replications and
  accounting fix: **4/10, weak reject**.


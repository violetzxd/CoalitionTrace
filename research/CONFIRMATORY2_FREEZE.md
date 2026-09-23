# Confirmatory-II freeze: independent scope-resolution family

Frozen before any model replay on these cases.  Confirmatory-I remains a failed,
fully reported attempt and is not replaced or augmented by this experiment.

## Independent data and partitions

- Datasets: SQuAD v1.1 development
  (`95aa6a52d5d6a735563366753ca50492a658031da74f301ac5238b03966972c9`)
  and the original
  WebQuestions test JSON mirrored by `brmson/dataset-factoid-webquestions`
  (`de320953700cd08300b9bcd2e60399da43b458a1be02db3f93c40344729fed39`).
  Neither dataset appeared in development or
  Confirmatory-I.
- Questions are normalized to lowercase ASCII alphanumeric tokens.  Exact
  normalized overlaps with every prior HotpotQA/NQ/MSMARCO/NQ2 case are removed.
  SQuAD is then frozen first; its 220 selected questions are also excluded from
  WebQuestions.  Within-dataset duplicate normalized questions retain only the
  first hash-ranked row.  The overlap audit must be zero.
- Eligible short-answer rows are sorted by SHA-256 of
  `confirmatory2-source|dataset:id`.  The first 40 per dataset are pilot-only;
  rows 40--219 (180 per dataset) are the sealed final pool.  Rows 220--439 are a
  disjoint target-donor pool and never serve as evaluated sources.
- Each evaluated source receives the first different answer encountered
  cyclically in that dataset's frozen donor pool.  Pilot and final target donors
  are therefore source-disjoint and fixed before replay.
- Models are the same pinned Qwen2.5-7B-Instruct and
  Mistral-7B-Instruct-v0.3 revisions used previously.

## New construction and pilot go/no-go

The all-active `confirmatory2-scope` family uses archival interpretation,
ordinary-scope disambiguation, and a scope-jurisdiction ruling.  It shares no
retrieved prompt-injection, integrity-defense, or revocation/restoration wording
with earlier families, but it remains in the broad suppressor/restorer Boolean
class and is not claimed as mechanism-independent generalization.  All eight
slots receive a deterministic full permutation derived only from
`(source_id,stratum,variant,"confirmatory2-slot-v1")`; planted causes and poison
indices are remapped.  Every one of the 256 masks must render to a distinct
complete request under both model chat templates.

Each source has one U, one A, and two N candidates in a fixed order.  Exhaust the
40-source pilot on both models.  Proceed to the sealed final pool only if every
dataset/model cell yields at least 20 realized N sources after method-blind
selection, at least 20 unique source IDs per dataset, and zero prompt collisions
or invalid oracle tables.  The pilot
may decide only go/no-go; it cannot change templates, method, budget, metrics,
or gates.  If it fails, Confirmatory-II stops.

## Frozen final evaluation

- Exhaust all 256 masks for every final candidate and retain the complete
  screening funnel.  Select at most one case per source/stratum in candidate
  order without method outputs.
- Required final floor: at least 50 N sources in every one of the four cells;
  at least 60 unique N source clusters per dataset and 120 across datasets; and
  at least 30 U and 30 A sources in every cell.  If any floor fails, the attempt
  is descriptive and the joint gate automatically fails.
- Methods: unchanged StandardEnumerator, prompt-uniform RandomResidualAudit,
  ShuffledSafeAudit, and the byte-identical frozen EWRA-Nearest implementation.
- Budget: 48 distinct rendered requests.  Seeds: integers 0--9.  U/A causes,
  enumeration-prefix queries, and ACEM must exactly match StandardEnumerator.
- Primary endpoint: N violation-detection recall, with seeds averaged within
  source and inference clustered by base `(dataset,source_id)` across models.
- Because this is the second confirmatory attempt, every paired gate uses the
  one-sided 97.5% lower bound, defined as the 2.5th percentile of 20,000 paired
  base-source cluster bootstraps with seed 20270920.  The two-baseline gate is
  intersection-union: both comparisons must pass, with no selection of the more
  favorable baseline.

## Joint success gate

All conditions must hold:

1. Nearest minus prompt-uniform is at least +0.05 and its paired 97.5% lower
   bound is greater than zero.
2. Nearest minus ShuffledSafeAudit has paired 97.5% lower bound greater than
   zero.
3. At least three of four cells have positive point effects against both
   baselines, and no cell is worse than prompt-uniform by more than 0.03.
4. Pooled Nearest recall is at least 0.88 and its 97.5% lower bound is at least
   0.83.
5. For the combined Confirmatory-I/II analysis, first average seeds within each
   model-case, then average available models within each base
   `(attempt,dataset,source_id)` cluster.  Each stratified bootstrap resamples
   base-source clusters independently within attempt, computes one pooled paired
   effect per attempt, and takes the equal-weight mean of the two attempt effects.
   With 20,000 resamples and seed 20270920, the 2.5th-percentile lower bound must
   exceed zero against both baselines.  In addition, each attempt's pooled point
   effect must be positive; Confirmatory-II retains the cellwise condition in
   gate 3.  Equal attempt weighting prevents the larger second study from
   washing out the failed first attempt.
6. U/A prefix identity, budget compliance, witness soundness, full artifact
   release, and the per-cell sample floors all pass.

No sequential extension, subset substitution, seed change, budget change, or
metric change is allowed after pilot or final labels are observed.

## Frozen implementation hashes

- `coalitiontrace/benchmark_confirmatory2.py`:
  `301fe7a53ebb930c84d104f35279076d18030ffdd4fb25168dc448ddc9f6dd45`
- `scripts/make_confirmatory2_benchmark.py`:
  `3bc5dcf4a09c5bad0d33999ee9af7883d43acd0750832b678074db52330a90e6`
- `scripts/preflight_confirmatory2.py`:
  `bf3d9b34a07ed3912fd7e9e4b13571366d6c031e40fa2582e3c97ba27bf1d091`
- `coalitiontrace/set_baselines.py`:
  `e5049bf923819a674750e571494ebb1ad69dd385b14c04c7514c6128a2a5a0c9`
- `scripts/evaluate_uan_oracles.py`:
  `ac83866bd136fab07c9eefcea7b35de2e6984a5e437774e268c4a9d1422743c0`
- `scripts/confirmatory2_statistics.py` (20,000-draw clustered gate and
  equal-attempt meta-analysis):
  `27f3e2e0d4ba1d714e6f2b227e80145ee4cc43bcff38932e86c8b4fe2e792fa6`
- `scripts/validate_confirmatory2_invariants.py` (U/A prefix identity, budget,
  and witnessed-violation soundness audit):
  `b5cdaa7f5db59342736c94c5a7d2ebb2bf2292f8b1ff9eccb31ce88b48fc88d9`
- `scripts/confirmatory2_pilot_gate.py` (aggregate-only feasibility gate; emits
  no case-level labels or method statistics):
  `b224febb4ead02320caa910907c82d634e29790298a6a293c9eb43f2df746a1d`
- SQuAD pilot/final case files:
  `6c45457c5a14bea841b39c457cc57fc14d32408a5d52df23f715402c3cd00a70` /
  `aa593fa38ba024689305d7fd435922b48830fd4958e8402f80b71c16301b6d87`
- WebQuestions pilot/final case files:
  `240a94a7364a23fa7f0e3ee6c10703b3d957e267e9279096e2a1f16cd76bc357` /
  `0678f4f67f949990c75a0248d7b278f2a3836493348dc17ffcf17bd19a534dd`
- Prior-question exclusion, selected-SQuAD question list, and their union:
  `22766dc77817b188b3cf866806c4586365a61b17d7a3326b2ea97c46c1c8f7fb`,
  `8d82749465efd74db3ace769f211c738fecb07b1bcc23f1e70d7387c9b6eb7ab`,
  `b7acf0c7cc6e69435a6bb4984ecfebb2034adf9c9028fc98cc82de67e53cc274`.

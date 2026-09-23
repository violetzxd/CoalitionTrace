# Frozen untouched holdout: nearest-cover residual audit

Frozen on 2026-09-20 before any generator replay on either holdout case file.
Registry, news, all-active, EWRA, and hybrid results are development evidence.

## Frozen artifacts

- `coalitiontrace/set_baselines.py` SHA-256
  `e5049bf923819a674750e571494ebb1ad69dd385b14c04c7514c6128a2a5a0c9`
- `coalitiontrace/benchmark_holdout.py` SHA-256
  `9c28fec58884376dcb48c210a721fcf74844f708ff31b940aabdefcecfb079d0`
- `scripts/make_holdout_benchmark.py` SHA-256
  `e8ae4379172be1440db4fb7b09e417194256227501da4aa7003b7f69132153ea`
- `data/holdout_msmarco_v1.jsonl` SHA-256
  `8a992328120286d6059a8f7a095abc0e2ccdb1ada08236a40472dd8ba3df8708`
- `data/holdout_nq2_v1.jsonl` SHA-256
  `5660971bec7534c7cd3a10d06b7ee1bc87abdcde034c9c6c2b337f161c4e6a8a`

Each case file has 70 sources and five candidates per source: one U, two A,
and two N candidates. All 256 masks at n=8 must render to distinct complete
chat prompts. MSMARCO test questions and a previously unused NQ confirmation
pool form the two datasets. Qwen2.5-7B-Instruct and
Mistral-7B-Instruct-v0.3 at the already pinned revisions form four cells.

## New mechanism and selection

The N candidates use retrieved prompt injection plus a retrieval-integrity
instruction, not the earlier revocation/restoration wording. U/A use a new
docket/finding template. Nominally noncausal slots also receive distinct
observed and replacement texts, so there is no literal prompt collapse.

Every candidate is exhaustively replayed before labeling. The realized truth
table, not the planted type, determines U/A/N. Within `(dataset, model, source,
realized stratum)`, retain the first candidate in file order. Selection may not
read any method output. Retain the complete construction funnel and every
excluded candidate. Required sample floor: at least 30 selected N sources in
each of four cells and at least 120 unique `(dataset, source)` N clusters pooled
across models. If a floor is missed, the holdout is descriptive and cannot pass.

## Frozen methods and endpoints

- Budget: 48 distinct complete-prompt SHA-256 classes.
- Seeds: integers 0 through 9, averaged within model-case and source cluster.
- Primary candidate: `EWRA-Nearest`, i.e. unchanged standard enumeration then
  nearest exposed comparable class, with fixed hash tie-breaking.
- Baselines: `RandomResidualAudit` (prompt-uniform without replacement) and
  `ShuffledSafeAudit`; `StandardEnumerator` verifies prefix preservation.
- Primary endpoint: realized-N violation detection. Pair by dataset/source and
  use a 20,000-draw source-cluster bootstrap.
- Secondary endpoints: residual query to first witness, total unique prompts,
  token cost, and multi-budget AUC. Holm-correct the secondary family.
- U/A safety endpoint: causes and `enumeration_queries` must equal Standard on
  every model-case at every reported budget.

## Acceptance gates fixed before replay

All gates must pass to claim method superiority:

1. Nearest minus Uniform is at least +.05 and its paired cluster-bootstrap 95%
   lower bound is greater than zero.
2. Nearest minus ShuffledSafeAudit has paired 95% lower bound greater than zero.
3. The effect is positive in at least three of four cells; no cell is worse than
   Uniform by more than .03.
4. Pooled N recall is at least .88 and its 95% lower bound is at least .83.
5. U/A causes and enumeration prefixes equal Standard exactly.
6. There is no budget overflow or false witness; report time-to-witness and
   prompt/token costs.

Failure of any gate forbids a method-superiority claim and forbids changing the
ratio, metric, source subset, seed panel, or budget. The theoretical minimax
analysis of prompt-uniform auditing remains independently testable and must not
be presented as evidence that Nearest passed.

# U/A/N benchmark and replay-results data card

## Purpose

The released artifacts support evaluation of minimal-cause attribution for a
fixed retrieval-augmented generation replay. They are intended for research on
faithfulness, ambiguity, prompt-equivalence accounting, and non-monotonicity
auditing. They are not a general-purpose question-answering dataset.

## Units and strata

Each benchmark case fixes a question, an answer target, an ordered context, a
contrastive replacement for each context slot, a generator revision, and a
deterministic decoder. Exhaustive replay over the small mask space induces a
Boolean utility function. Cases are labeled from this *realized truth table*,
not from the construction template:

- **U:** one inclusion-minimal sufficient cause under monotone replay;
- **A:** two or more alternative inclusion-minimal sufficient causes under
  monotone replay;
- **N:** at least one realized monotonicity violation.

## Released content

`results/*.jsonl` contains one evaluation record per case, method, budget, and
seed. Common fields include `case_id`, source dataset, model alias, U/A/N
stratum, method, query counts, unique rendered-prompt counts, cause precision,
recall and F1, exact cause-set match (ACEM), detected non-monotonicity, and the
applicable completeness flags. `results/final_delivery/` contains compact
aggregates and manifest files used by the paper.

The release contains identifiers and derived measurements, not the raw source
documents, questions, model outputs, prompts, or model checkpoints. Normalized
question lists under `data/manifests/` support exclusion and leakage checks.

## Source data and models

The experiments derive cases from HotpotQA and Natural Questions, with SQuAD
and WebQuestions used in exclusion checks. Users must obtain those datasets
from their original sources and comply with their licenses and terms. The
generator checkpoints are pinned revisions of Qwen2.5-7B-Instruct and
Mistral-7B-Instruct-v0.3; their hashes are listed in `REPRODUCIBILITY.md`.

## Collection and labeling

All labels are computed programmatically from frozen deterministic replays.
Every candidate cause is verified for sufficiency and member necessity. For
the studied small contexts, the full mask space is retained as an immutable
oracle table before any search or audit method is scored. Byte-identical
rendered prompts are treated as one physical generator call.

## Known limitations

- The benchmark is conditional on its prompts, replacement construction,
  decoder, exact-match target rule, and two 7B instruction-tuned generators.
- U/A/N frequencies are construction-dependent and are not population
  estimates for deployed RAG systems.
- Non-monotonicity detection is budgeted; failure to find a violation is not a
  certificate that none exists.
- Source-clustered confidence intervals are required because multiple cases or
  seeds can share a source question.
- Model and dataset license terms are not transferred by this artifact.

## Privacy and sensitive information

No credentials, private server paths, or personally identifying participant
data are intended to be present. The source benchmarks are public research
datasets; this repository publishes only derived identifiers and measurements.


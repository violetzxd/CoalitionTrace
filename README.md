# CoalitionTrace

Official research artifact for **“When Does Leave-One-Out Suffice? Auditing
Minimal-Cause Attribution in RAG”** (ICASSP 2027 submission).

CoalitionTrace asks a deliberately narrow question: for a fixed retrieved
context, generator, decoder, replacement rule, and target answer, which
document sets are *inclusion-minimal sufficient causes* of that answer? The
project separates three objects that are often conflated:

1. deterministic, slot-preserving model replays;
2. the resulting Boolean utility table, which is the experimental oracle; and
3. attribution/search procedures evaluated against that oracle.

The U/A/N benchmark covers unique monotone causes (U), alternative monotone
causes (A), and realized non-monotone behavior (N). Ground truth for the small
contexts studied in the paper is obtained by exhaustive mask evaluation,
including mixed clean/contrastive subsets. Reported causes must pass both
sufficiency and member-necessity checks.

## Main result in one paragraph

Under monotone replay, grand-coalition leave-one-out (LOO) identifies a unique
minimal cause, but with alternative causes it recovers only their common
intersection. Correct accounting must charge distinct rendered prompts rather
than nominal masks, because multiple masks can collapse to the same model
input. Our enumerate-first, prompt-uniform residual audit protects all-cause
enumeration and uses only the remaining physical-call budget to search for
non-monotonicity. It achieves perfect U/A recovery in the reported fully
oracled evaluation and substantially improves raw-N violation recall, while the
no-collapse and frozen-holdout results document its limits. A finite trace with
no violation is therefore diagnostic evidence, not a monotonicity certificate.

## Repository map

- `coalitiontrace/`: reusable algorithms, replay accounting, and metrics.
- `scripts/`: benchmark construction, evaluation, audits, statistics, and plots.
- `tests/`: unit and exhaustive small-instance checks.
- `results/`: claim-level summaries plus the row-level metrics required to
  recompute the reported uncertainty estimates.
- `data/manifests/`: SHA-256 question-exclusion digests; no third-party
  benchmark text is redistributed.
- `research/`: frozen protocols, theorem notes, deviations, and claim ledger.
- `paper/`: LaTeX source, figures, bibliography, and compiled manuscript.

## Quick start

Python 3.10 or newer is required. The frozen experiments used Python 3.12.

```bash
conda env create -f environment.yml
conda run -n coalitiontrace python -m pytest -q
```

For an existing compatible environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The public result tables can be regenerated without model weights:

```bash
python scripts/analyze_uan.py --help
python scripts/analyze_stable_n.py --help
python scripts/plot_audit_results.py --help
python scripts/plot_safe_frontier.py --help
```

Model replay requires the optional GPU dependencies and locally obtained model
checkpoints. Exact model revisions, decoding settings, and host software are
recorded in `REPRODUCIBILITY.md`; the frozen experimental protocol is in
`research/AMBIGUITY_PIVOT_PROTOCOL.md`.

## Data and provenance

This repository releases derived manifests, pseudonymous identifiers, costs,
predictions, and evaluation metrics needed to audit the paper's claims. It
intentionally does not redistribute the raw HotpotQA, Natural Questions,
SQuAD, or WebQuestions corpora, model prompts/outputs, or Qwen/Mistral weights.
Obtain those assets from their original maintainers under their respective
terms, then use the included construction scripts and hashed question-exclusion
lists. See `DATA_CARD.md` for field definitions, scope, and limitations.

## Reproducing the paper

The manuscript compiles from `paper/main.tex` with the included ICASSP style,
bibliography, and PDF figures. The checked-in `paper/main.pdf` is the exact
public artifact version. Statistical claims should be traced through
`research/CLAIM_RESULT_MANIFEST.md` and `research/RESULTS_LEDGER.md` before use.

## Licenses

Source code is released under the MIT License (`LICENSE`). Derived manifests
and numerical result tables are released under CC BY 4.0 (`LICENSE-DATA`).
Third-party datasets, model weights, ICASSP style files, and cited works remain
subject to their original terms and are not relicensed here.

## Responsible use

CoalitionTrace is an evaluation and auditing artifact, not a guarantee that a
deployed RAG system is monotone, safe, or causally identified. Its conclusions
are conditional on the frozen model, prompt rendering, contrastive replacement,
decoder, target-answer rule, and tested budget. Do not interpret an unviolated
finite audit as proof of global monotonicity.

## Citation

Please cite the accompanying manuscript. Machine-readable author metadata is
provided in `CITATION.cff`.

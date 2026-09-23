# Frozen pivot protocol (investigator-approved 2026-09-20)

Working title: **When Does Leave-One-Out Suffice? Ambiguity-Aware Minimal-Cause
Attribution in Retrieval-Augmented Generation**

This protocol supersedes the original positive CoalitionTrace hypothesis after its
preregistered pilot failed.  It is not a post-hoc relabeling of the v2/v3 results:
all primary results require new, position-randomized data and new endpoints.  The
old results are retained only as motivation and an auditable negative pilot.

## Formal target

For a fixed replacement intervention and thresholded replay utility
`v_tau(S) = 1[v(S) >= tau]`, recover the set of inclusion-minimal sufficient causes
`M(v_tau)`, not only one minimum-cardinality mask.  Report:

- any-cause exact match;
- all-cause recall and precision over a set of sets;
- false-cause rate after real sufficiency/minimality replay;
- ambiguity `|M(v)|` and the LOO backbone;
- total generator calls, scored answer tokens, and wall-clock time.

The primary utility is deterministic greedy-generation normalized exact match
after a frozen format-only extractor (optional `Answer:` prefix, later lines, and
trailing provenance parenthetical),
which gives an auditable Boolean replay table. Teacher-forced, length-normalized
target-versus-clean answer log-likelihood margin is a mandatory robustness
measurement. N classification uses the Boolean table, while `stable-N` additionally
requires the violation to persist under the preregistered intervention/order audit
and to be directionally supported by the continuous margin; one unstable decoded
string is not treated as robust evidence.

The LOO boundary propositions are frozen in `LOO_BOUNDARY_THEOREM.md` before new
method evaluation.

## Required strata

- `U`: monotone utility, one inclusion-minimal cause;
- `A`: monotone utility, at least two alternative minimal causes;
- `N`: non-monotone thresholded utility under the declared replacement
  intervention, confirmed by at least one subset/superset violation whose
  continuous margin change exceeds the preregistered tolerance.

Each primary model/data stratum requires at least 100 independent test queries
after screening, with screening yield and exclusions reported. Slots are
independently permuted by a case-derived seed. Templates, entities, questions and
generation seeds are split before screening. HotpotQA and Natural Questions form
separate data strata. Small (`n<=10`) cases have exhaustive oracle tables; larger
`n in {16,32}` cases use hidden construction labels plus replay verification and
are never used for claims of exhaustively known global ambiguity.

## Proposed algorithm

1. Query empty, full and all full-context leave-one-out masks.
2. If the LOO candidate passes direct sufficiency and member-necessity validation,
   return it with a **conditional certificate under an explicit monotonicity
   assumption**.  Budgeted checks alone must never be described as proving global
   uniqueness.
3. If LOO is empty/ambiguous, run cached exclusion-guided minimization.  Each
   discovered cause creates branches that exclude one non-backbone member; under
   monotonicity and an unlimited budget this enumerates every inclusion-minimal
   cause. Balanced group probes prioritize branches but do not alter correctness.
4. If observed probes contradict monotonicity, withdraw the monotone certificate
   and switch to budgeted general subset search (or abstain when no verified cause
   is found).
5. Continue until the requested cause coverage is achieved or return an explicit
   budget-relative ambiguity certificate; never claim a unique global cause when
   alternatives remain unexcluded.

## Locked go/no-go criteria

- `U`: match LOO accuracy and add no more than the validation calls needed for the
  certificate.
- `A`: all-cause recall at least 10 percentage points above LOO and single-cause
  deletion baselines, with a 95% query-level paired bootstrap CI excluding zero.
- `N`: verified any-cause ECM at least 10 percentage points above LOO, or a
  preregistered selective-risk result showing materially safer abstention at
  matched coverage. N is not pooled with A to rescue a failed endpoint.
- Overall verified-cause validity at least .95 and false-cause rate at most .05.
- Compare against assertion-tested KernelSHAP, classic ddmin, greedy deletion,
  repeated-deletion enumeration, LOO, and random group testing at matched unique
  replay budgets.
- Results must hold over at least 10 case-derived algorithm seeds and two generators.

If these gates fail, retain the work as a negative benchmark/theory report rather
than submitting a positive ICASSP regular paper.

## Leakage and independence controls

- No test case may be selected because the proposed method succeeds on it.
- Screening uses oracle properties only and is completed before method seeds run.
- A source question, answer entity, template instance, and all derived variants
  belong to exactly one split.
- Replacements preserve slot count and approximate length, contain neither target
  nor clean answer strings, and are audited for accidental answer cues.
- The statistical unit is the source query, not a mask, replay, or random seed.
- All failures, exclusions, prompt templates, model revisions, and hashes are
  retained in the artifact manifest.

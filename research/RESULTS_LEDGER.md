# Final-results ledger

This ledger records source-level results used in the ICASSP manuscript. Values
are never copied from console output without a corresponding immutable JSON
artifact. Post-hoc extensions are marked explicitly.

## Registry A, budget 48 unique rendered prompts

| Dataset | Model | n | Adapt ACEM/prompts | StdEnum ACEM/prompts | Repeated ACEM/prompts | Random ACEM/prompts |
|---|---:|---:|---:|---:|---:|---:|
| HotpotQA | Qwen | 58 | 1.000/13.0 | 1.000/12.4 | .905/13.0 | 1.000/15.7 |
| NQ | Qwen | 49 | 1.000/14.6 | 1.000/14.2 | .904/14.2 | .920/18.4 |
| HotpotQA | Mistral | 54 | 1.000/12.9 | 1.000/11.9 | .913/13.1 | .981/15.4 |
| NQ | Mistral | 52 | 1.000/14.1 | 1.000/12.8 | .931/13.4 | .983/15.8 |

LOO ACEM is 1.000 on registry U and 0 on registry A in every cell. Registry
source counts `(U,A,N)` are Hotpot/Qwen `(56,58,58)`, NQ/Qwen `(49,49,45)`,
Hotpot/Mistral `(58,54,60)`, and NQ/Mistral `(53,52,59)`. Frozen-adaptation raw
N detection recall is `.552/.511/.383/.492` in the same order.

Artifacts: `summary_uan_registry_fair.json`, `stats_ambi_vs_*_final.json`.

## Accounting correction

Registry A contains only 15.7--19.8 unique prompts per 256 masks on average.
For Qwen Hotpot/NQ, Adapt-minus-Repeated ACEM changes from `.205/.202` under the
withdrawn mask budget to `.095/.096` under prompt accounting. Random-mask ACEM
changes from `.000/.000` to `1.000/.920`. Fair Adapt input-token means are
10,011 and 9,673 per source; corresponding Repeated means are 9,980 and 9,285.

Artifact: `accounting_shift_qwen.json`.

## Frozen news wording robustness

All four A cells retain Adapt and StdEnum ACEM 1.000. Repeated ranges
`.898--.968`; Random ranges `.943--.976`; A source counts are 53, 40, 45, and 38
for Hotpot/Qwen, NQ/Qwen, Hotpot/Mistral, and NQ/Mistral. The final cell misses
the 40-source floor and is descriptive.

Artifact: `summary_uan_news_fair.json`.

## Post-hoc n=10 scaling check

Qwen Hotpot/NQ A source counts are 40/27 and Mistral counts are 34/32. Across
all four cells only `.017--.021` of the 1,024 masks are distinct prompts on
average. Adapt/StdEnum are tied at 1.000 ACEM in every cell, while StdEnum uses
13.05/14.93 prompts versus 13.68/15.37 for Qwen and 12.3/12.8 versus 13.8/14.0
for Mistral. Repeated obtains .893/.900/.909/.916 and Random
.950/.889/.971/.969 in Qwen-Hotpot/Qwen-NQ/Mistral-Hotpot/Mistral-NQ order.
Only Qwen-Hotpot reaches the 40-source floor; the other cells are descriptive.

Artifacts: `summary_uan_n10_{qwen,mistral}_fair.json`.

## Post-hoc all-active control

Every mask is a distinct prompt. For Qwen, only 9/200 Hotpot and 5/200 NQ
planted-A candidates realize as A, while 119/200 and 93/200 realize as N. For
Mistral, A/N candidate counts are 4/131 and 4/128. After one-case-per-source
selection, A has only 6/5/3/4 sources in Qwen-Hotpot/Qwen-NQ/Mistral-Hotpot/
Mistral-NQ order. The cells are too small for method comparison; they establish
that removing prompt equivalence by activating every slot changes the realized
oracle structure. For completeness, the stored descriptive results show both
enumerators at 1.000 ACEM in all four tiny cells, with StdEnum point-estimate
costs below Adapt; these values are not used as performance evidence.

Artifacts: `uan_*_active_*_manifest.json`, `summary_uan_active_fair.json`.

## Post-hoc stable-N audit

Stability requires a margin-separated violating edge and persistence of N under
both order permutation and independently worded replacement. Stable/detected
counts are Hotpot/Qwen 10/9, NQ/Qwen 1/1, Hotpot/Mistral 3/1, and NQ/Mistral
6/1. Pooled only as a descriptive safety summary, the frozen method detects
12/20 stable cases (Wilson 95% CI [.387,.781]), below the .80 target. The robust
subset is too small for high-precision cellwise estimates and is not used to
relabel the primary realized oracle.

Artifacts: `stable_n_{hotpot,nq}_{qwen,mistral}.json`.

## Post-hoc enumerate-first residual audit

The final wrapper runs StandardEnum unchanged, then uniformly samples unseen
rendered-prompt equivalence classes using only its residual budget. At budget 48,
ten-seed mean registry N recall is `.943/.922/.943/.980` in Hotpot/Qwen,
NQ/Qwen, Hotpot/Mistral, NQ/Mistral order. Averaging model outcomes within each
dataset/source cluster gives `.952` over 130 clusters (222 model-cases), with a
cluster bootstrap interval `[.930,.972]`. StandardEnum's clustered incidental
detection is `.388`; the paired gain is `.563 [.495,.630]`. Registry U/A ACEM
remains 1.000. Enumeration consumes 16.43 unique prompts on N per cluster on
average, the residual audit 4.67, and detected witnesses appear after 4.05
residual prompts on average.

The frozen implementation transfers to the news-wording family at `.950`
`[.929,.968]` clustered N recall and 1.000 A ACEM. On the no-collapse all-active stress
set it falls to `.814` `[.753,.869]`, while retaining 1.000 A ACEM on the tiny
18-case A cohort. Directional/ordering ablations on registry N are upward `.797`,
downward `.667`, deterministic cover `.935`, and shuffled cover `.948`. Thus the
supported contribution is an enumeration-preserving residual-budget wrapper,
not a uniquely superior boundary heuristic or a monotonicity certificate.

Artifacts: `uniform_*.jsonl`, `uniform_curve_*.jsonl`,
`safe_ablation_*.jsonl`, `residual_audit_statistics.json`.

Prompt-class closure is mandatory: replaying one prompt hash propagates its value
to every equivalent mask before searching the mask lattice for a violation. The
quotient is used for accounting only and need not inherit the subset order.
After this correction, the headline randomized-audit cell recalls are unchanged;
cover-ablation values above are the recomputed closed-class results.

No experimental result used by the manuscript remains pending.

## Post-submission-candidate algorithm iteration (development only)

An exposure-weighted residual audit (EWRA) was evaluated after the manuscript's
uniform audit had already been inspected. Across 571 dataset/source clusters in
the combined registry, news-wording, and all-active development corpus, all four
EWRA score variants obtained .815 N-violation recall. Prompt-uniform and
shuffled-cover audits obtained .912 and .913. The paired EWRA--Uniform effect was
-.096 (source-cluster bootstrap 95% CI [-.117,-.076]); EWRA--shuffled-cover was
-.097 [-.120,-.076]. Mean total queries were 27.69 for EWRA and 24.49 for
Uniform. This is a negative result and cannot support a paper claim. A second,
explicitly development-only panel of inverse-depth and hybrid policies was
frozen in the idea log before execution.

Artifact: `ewra_dev_summary.json` (GPU result directory; to be copied into the
release bundle after the development panel closes).

The predeclared second development panel found that sparse-exposure and nearest-
cover scheduling induce the same query order on this corpus. Both obtain .945
pooled N recall, compared with .912 for prompt-uniform and .913 for shuffled
cover. Source-cluster paired differences are +.033 [.021,.047] and +.032
[.019,.045], respectively. Total prompts fall from 24.49 (Uniform) to 23.12 and
the detected witness moves from residual query 3.98 to 2.97. Fixed 25/50/75%
hybrids obtain .909/.910/.908 and are rejected. One NQ/Mistral all-active cell
is 4.2 points below Uniform, and the pooled gain is below the five-point gate;
therefore these remain development results. Nearest alone was frozen for a new
no-collapse holdout before replay.

The first static-witness analysis was invalidated before paper use: it assigned
zero audit probability when the standard enumeration prefix had already found a
violation, creating a spurious .044 ``dynamic'' excess, and its regime-coded
dataset key duplicated base sources. The corrected analysis sets the lower bound
to one for prefix detections, clusters across construction variants and models
by base dataset/source, and uses 1,000 offline random permutations per case.
Across 571 N model-cases / 138 base-dataset/source clusters, the fixed-prefix
hypergeometric lower bound is .920872 and simulated sequential prompt-uniform
detection is .920959. Their difference is .000087 with cluster-bootstrap 95% CI
[-.000030,.000495]; no detection among the 571,000 runs required a dynamically
created comparable relation. Thus the finite-population expression essentially
exactly explains this development corpus. Only this corrected artifact may be
cited; the earlier numbers are retained above solely as an audit trail.

Artifacts: `ewra2_dev_summary.json`, `uniform_minimax_1000_v2.json`, and
`NEAREST_HOLDOUT_FREEZE.md`.

## Frozen Confirmatory-I holdout (2026-09-20; failed gate)

All four exhaustive oracle tables completed before labels were revealed (89,600
rows per dataset/model cell).  The method-blind selector retained 67/64 N cases
for MSMARCO with Mistral/Qwen, but only 15/16 for the unused NQ confirmation
pool.  The preregistered minimum of 30 N cases per cell therefore failed and,
by the frozen protocol, all following results are descriptive rather than a
successful confirmatory test.

At budget 48 with ten fixed seeds, EWRA-Nearest achieved pooled N detection
0.8352 (cluster bootstrap 95% CI [0.7815, 0.8864]), versus 0.7975 for the prompt-
uniform audit and 0.8074 for ShuffledSafeAudit.  Paired differences were +0.0377
[0.0037, 0.0716] and +0.0278 [-0.0086, 0.0642], respectively.  Cell differences
against prompt-uniform were +0.0104, +0.0688, +0.0800, and -0.0125 for MSMARCO/
Mistral, MSMARCO/Qwen, NQ2/Mistral, and NQ2/Qwen.  Thus the frozen conjunction
also failed the >=+0.05 effect-size requirement, the positive lower bound against
the stronger shuffled baseline, the pooled recall >=0.88 requirement, and the
cross-cell robustness requirement.  This attempt must be reported in full and
must not be repaired by adding cases after label reveal.

## Confirmatory-II feasibility pilot (2026-09-20; prespecified STOP)

After Confirmatory-I failed, a separately frozen second attempt used new,
source-disjoint SQuAD and WebQuestions pools and a new scope-resolution surface
construction. Before replay, the protocol required at least 20 realized N
sources in every dataset--model pilot cell and allowed disclosure only of N
yield, unique-source counts, collision/validity counts, and GO/STOP. The four
cell yields were 14 (SQuAD/Qwen), 13 (SQuAD/Mistral), 19
(WebQuestions/Qwen), and 14 (WebQuestions/Mistral). Unique realized-N source
counts were 22 for SQuAD and 23 for WebQuestions. All 163,840 oracle rows were
complete; request collisions and invalid tables were both zero. Because every
cell missed the floor, the frozen decision is STOP. The sealed final pool was
not replayed, no method comparison was run on the pilot, and the construction
will not be modified and retried as Confirmatory-II. The aggregate gate
artifact SHA-256 is
`2e6403a62c4b6c33a1cfdf5c36f2f795c1fae252da1a693d6ec96cadd1f53e29`.

## Non-selective construction-realizability audit

Following the two stopped confirmation attempts, an outcome-independent audit
enumerated every stored `*analysis*.jsonl` artifact in the server snapshot: 34
analysis artifacts and 14 Qwen--Mistral paired comparisons. For every artifact
it reports complete-table U/A/N/OOS counts and 20,000-draw base-source cluster
bootstrap intervals; for every name-matched model pair it reports exact
case-level stratum agreement with the same source-cluster resampling.
Confirmatory-II is included only through its aggregate frozen
feasibility gate, because its per-case labels were deliberately never emitted.
No family or outcome was filtered. The machine-readable artifact is
`results/construction_yield_audit_all.json`, SHA-256
`0ea4aca5bdbdd7aaf2d992c4652b0c867f693076de2558815bca6b8afb9e65b2`.

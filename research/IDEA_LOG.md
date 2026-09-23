# Experiment and decision log

This file is append-only after the pivot freeze.  Entries distinguish hypotheses
from results so that unsuccessful ideas remain visible.

## 2026-09-20 — authorized pivot

- **Observation:** exhaustive v3 pilots produced no A cases and showed that LOO or
  hierarchical deletion dominates the original interaction-search method on the
  intended pair task.
- **Decision:** withdraw the claim that scalar LOO misses a unique monotone
  coalition.  Target all inclusion-minimal causes instead.
- **Hypothesis H1:** grand-coalition LOO is an optimal fast path on U and returns
  only the common backbone on A.
- **Hypothesis H2:** cached exclusion-guided minimization can enumerate A causes
  with substantially higher all-cause recall than single-output baselines at a
  matched replay budget.
- **Hypothesis H3:** many apparent N cases from decoded exact match are generation
  noise.  Contrastive teacher-forced margins plus a tolerance will yield a more
  reproducible N stratum.
- **Rejected idea:** treat a validated LOO mask as proof of global uniqueness
  without a monotonicity assumption.  Finite probes cannot provide that proof.
- **Rejected idea:** pool A and N improvements.  Their assumptions and failure
  modes differ and they require separate endpoints.
- **Next tests:** exact synthetic U/A/N unit tests; exhaustive `n<=10` LLM oracle;
  two data sources, two frozen generators; `n=16/32` transfer with only local
  verification claims.

## 2026-09-20 — first U/A/N full-table pilot

- **Result (Qwen, HotpotQA, 14 candidates, n=8):** 1 A, 5 N, 8 out of scope,
  and 0 U under the exact Boolean oracle. This is the first realized A case, but
  the yield is far below the frozen target and is not confirmatory evidence.
- **Diagnosis:** same-query retrieved passages often state the clean answer. They
  interact with the planted target paths, suppress full-context attacks, and
  create many construction-induced N cases. The realized A cause sizes (4--5)
  also show that these documents enter the oracle causes.
- **Revision R1:** U/A candidates will use answer-scrubbed donor passages from
  different source queries as matched realistic distractors. Same-query clean
  evidence is retained as a conflict-control family and for intentional N, not
  mixed into the monotone U/A construction.
- **Falsification condition:** if R1 still yields fewer than 20% realized A or
  produces mostly N, abandon template scaling and redesign the intervention.
- **Measurement revision R2:** Mistral frequently appended parenthetical passage
  provenance despite the exact short-answer instruction (for example, a correct
  target followed by “according to ...”), turning formatting into false failure.
  Before confirmatory data, freeze a format-only extractor that strips an
  `Answer:` prefix, later lines, and a trailing parenthetical. Raw generations are
  retained. No aliases or semantic judge are used in the primary Boolean label.
- **Intervention revision R3:** R1 still produced 6 N, 7 out-of-scope, 1 U and
  0 A among 14 Qwen candidates. Inspection showed that nominally inactive clean
  slots swapped between two different unrelated donor passages, so masks changed
  more than the candidate causal evidence. Freeze noncausal slots as identical in
  observed and replacement contexts. Only causal slots now change between a
  structured document and a length-matched inert document. A separate replacement
  sensitivity audit will vary the inert document; it is not mixed into the primary
  U/A oracle.
- **Pilot R3 result (Qwen/HotpotQA, n=8, 14):** 2 A, 1 U, 4 N and 7 OOS.
  Both A-size-2-disjoint candidates realized A; one had three oracle causes due
  cross-path recombination, a useful ambiguity pattern rather than planting
  failure. At budget 32, exclusion enumeration ACEM was .50 versus mean .60 for
  ten-order repeated greedy; at budget 64 both reached 1.0, but enumeration used
  37 versus about 59 calls. This misses the frozen accuracy gate at 32.
- **Algorithm revision R4:** replace linear single-document minimization inside
  each exclusion node with balanced chunk deletion followed by exact single-item
  validation. Hypothesis: preserve completeness while moving the full A recovery
  point below 32 calls. This comparison was motivated by the development pilot and
  must be frozen before confirmatory test cases.
- **R4 development check:** at budget 48, AmbiCause reached A ACEM 1.0 versus
  repeated-greedy mean .80 on the two-case Qwen development set, using 34.5 calls;
  at 64 both were 1.0 but repeated greedy used about 59 calls. Freeze 48 as the
  primary small-n budget; this is only a development observation.
- **Confirmatory construction profile:** upweight U-size2/3 and A-size2-disjoint,
  retain A-size3 and explicit N for screening, and preserve all failures. Exact
  duplicate prompts caused by fixed background slots may be evaluated once under
  deterministic decoding and copied to their masks; the prompt hash and group
  size are stored, so this is lossless computation reuse rather than imputation.

## 2026-09-20 — first held-out cell and safety-mode follow-up

- **Held-out NQ/Qwen (registry family):** source-level selection yielded U=49,
  A=49, N=45 from 70 test sources. At budget 48, AmbiCause A ACEM=.959 and
  cause-F1=.994 with 34.9 calls; ten-seed repeated greedy averaged ACEM=.757 and
  F1=.953 with 47.9 calls. U ACEM was 1.0 for AmbiCause and LOO.
- **Failed gate:** observed-N detection was .511, below the frozen .80 target.
  This failure is retained and the original confirmatory method is not modified.
- **New follow-up hypothesis (safety mode):** after finding a sufficient cause,
  explicitly test each cover edge obtained by adding one excluded document.
  This targeted upward audit should expose suppressors missed by downward
  minimization, at up to `n-|C|` extra calls. It is a separately named safety
  mode, developed after the first held-out result; it cannot replace that result.
  Any positive claim requires a new untouched construction-family evaluation.

## 2026-09-20 — second held-out Qwen cell and revised paper claim

- **Held-out HotpotQA/Qwen (registry family):** source-level selection yielded
  U=56, A=58 and N=58 from 70 test sources. At budget 48, the frozen AmbiCause
  method reached A ACEM=1.000 and cause-F1=1.000 with 31.8 calls. Ten-seed
  repeated greedy averaged ACEM=.795 and cause-F1=.964 with 48.0 calls. U ACEM
  was 1.000 for both AmbiCause and LOO.
- **Paired primary comparison:** against frozen repeated-greedy seed 0, the A
  ACEM difference was +.138 (95% source-bootstrap CI [.052,.224]); exact
  McNemar p=.0078125. NQ/Qwen gave +.143 [.041,.265], p=.0390625. Holm-adjusted
  p-values are deferred until all four dataset--model cells finish.
- **Replicated failed safety gate:** frozen AmbiCause detected only .552 of
  observed N cases. The post-hoc upward-audit variant improved this to .707 at
  budget 48 (.724 at 64) but reduced A ACEM to .828. It therefore fails both the
  predeclared N-detection target (.80) and the primary A result, and will not
  replace the frozen method.
- **Paper-scope decision:** the defensible positive claim is restricted to exact
  U/A oracles under monotonicity: LOO is sufficient for U and returns only the
  common backbone for A; exclusion-guided enumeration improves all-cause recovery
  in A. N is a stress stratum demonstrating why finite black-box traces cannot
  certify monotonicity. No claim of solving non-monotone attribution will be made.
- **New experiment idea I1 (margin-stable N):** re-evaluate only observed
  violating cover edges with teacher-forced target-versus-clean log-probability
  margins. Report how many Boolean N cases survive a predeclared numerical
  tolerance; do not use the audit to relabel primary U/A cases.
- **New experiment idea I2 (construction transfer):** use the already frozen
  `news` wording family as a descriptive robustness set. This tests whether U/A
  yield and the budget frontier depend on registry-specific wording; it is not a
  second independent sample because source questions overlap.
- **New experiment idea I3 (large-n scaling):** generate exact monotone DNF
  utilities with known alternative causes for n=16 and n=32. Compare calls and
  ACEM without claiming LLM realism. This isolates enumeration scaling from
  generator stochasticity and avoids infeasible 2^n oracle tables.
- **New experiment idea I4 (replacement sensitivity):** on a source-disjoint
  subset, resample two inert replacements per causal slot and measure stratum
  agreement and cause-set Jaccard. This directly audits whether causes are
  properties of the contrastive intervention rather than of the observed text
  alone.

## 2026-09-20 — prompt-equivalence correction and method no-go

- **Independent-review finding:** masks that toggle fixed noncausal slots render
  to byte-identical prompts. The original online evaluation cached by mask and
  therefore charged repeated generator work that a deployable implementation
  would reuse exactly. The old 31--35 versus 48 replay-cost comparison is
  withdrawn.
- **Corrective protocol:** all methods now share a SHA-256 rendered-prompt cache;
  the budget counts unique prompt hashes and the output separately records masks
  touched. The original mask-budget results remain only as a retrospective audit.
- **Corrected Mistral results at 48 unique prompts:** on HotpotQA/NQ A,
  AmbiCause ACEM=1.000/1.000, RandomMasks=.981/.981 and ten-seed
  RepeatedGreedy=.913/.931. AmbiCause's gains over repeated greedy are below the
  frozen 10-point practical threshold and its gain over random masks is only 1.9
  points. The method-superiority hypothesis is rejected.
- **Strong baseline result:** a standard monotone exclusion/hitting-set
  enumerator with the same balanced minimizer matches AmbiCause ACEM=1.000 and
  uses fewer prompts on the completed HotpotQA/Mistral and NQ/Qwen cells. Any
  algorithmic novelty claim is terminated; AmbiCause remains only an audited RAG
  adaptation.
- **Reframed hypothesis H4:** syntactic mask accounting can change apparent
  attribution efficiency and ranking when interventions have identical rendered
  prompts. This is currently a construction-local observation, not a general
  claim. It survives only if registry results replicate across both generators
  and an all-active control clarifies the fixed-slot confound.
- **All-active control:** every slot receives distinct observed/replacement text,
  and acceptance requires all `2^n` prompt hashes. Run it separately without
  pooling. If the accounting effect disappears, state that prompt equivalence
  was an avoidable benchmark-design artifact.
- **Theory addition:** a trace-level indistinguishability proposition now states
  when an unqueried comparable mask admits both monotone and non-monotone
  completions. It is not presented as a new general property-testing lower bound.

## 2026-09-20 — reviewer-gated audit endpoint

- **Primary claim after correction.** The publishable result is a boundary and
  evaluation audit, not a new enumerator: LOO is exact for a unique monotone
  cause, returns the backbone with alternatives, and a finite unviolated trace
  is not a general monotonicity certificate. Standard exclusion enumeration
  matches the RAG fast-path adaptation and is usually cheaper.
- **Prompt-cost lesson.** Budgets are charged to complete rendered-chat-prompt
  hashes; masks touched and input/output tokens are reported separately. In the
  registry A cells only 6.1--7.7% of 256 masks are distinct prompts.
- **Stable-N rule.** Raw realized N remains primary. The exploratory robust
  subset additionally requires a violating cover edge with at least 0.25 nats
  target-versus-clean margin at both endpoints and persistence under both order
  permutation and independently worded neutral replacement.
- **Scaling check.** The $n=10$ A-only cohort tests whether $n=8$ saturation
  hides separation. It is descriptive because it was added after registry
  results; source query remains the sampling unit.
- **Follow-up idea.** Define the intervention quotient before attribution. A
  later benchmark could contrast literal rendered-prompt equivalence with
  semantic near-equivalence and test whether approximate quotienting preserves
  replay outcomes without using labels.

## 2026-09-20 — scaling and intervention-validity follow-ups

- **Observed $n=10$ behavior.** The first powered Qwen/Hotpot cell retains 40
  method-blind A sources. At 48 unique prompts, the RAG adaptation and standard
  enumerator both obtain ACEM 1.000, while standard enumeration is slightly
  cheaper (13.05 versus 13.68 prompts). This reinforces the audit conclusion:
  adding nominal slots does not create algorithmic separation when the prompt
  quotient remains small (18.4 of 1,024 masks on average).
- **New idea I5 (activity-controlled path).** Rather than switching directly
  from fixed neutral slots to an all-active context, activate 0, 25, 50, 75,
  and 100 percent of nominally neutral slots with source-matched distractors.
  Measure transitions among U/A/N and the prompt quotient at each level. This
  would distinguish an accounting effect from an intervention-semantics phase
  transition.
- **New idea I6 (two-axis benchmark card).** Report every causal benchmark on
  two independent axes: oracle structure (cause count, overlap, size and
  monotonicity) and intervention geometry (literal quotient size, semantic
  replacement distance and order stability). Matching only the planted oracle
  structure is insufficient when replacement choices change realized labels.
- **New idea I7 (sequential safety abstention).** Use margin and perturbation
  checks only to decide whether to abstain from a monotone completeness claim,
  never to relabel N as A/U. Calibrate an abstention threshold on a separate
  development split and evaluate coverage versus stable-N violation recall on
  untouched sources.

## 2026-09-20 — residual-audit iteration

- **I8 (implemented): enumerate-first prompt-uniform audit.** Preserve the
  standard enumerator's full prefix, then sample unseen rendered-prompt classes
  uniformly. This separates the all-cause objective from safety detection and
  prevents duplicated masks from biasing the audit schedule.
- **I9 (implemented ablation): audit geometry.** Compare random unseen prompt
  classes, upward-only, downward-only, deterministic cover expansion, and
  shuffled cover expansion under the identical enumeration prefix and physical
  prompt budget. The result shows no unique boundary-heuristic advantage;
  residual budget is the main effect.
- **I10 (next benchmark): distance-stratified N.** Generate N cases with a frozen
  distribution over the shortest trace-to-witness distance and violation-edge
  density, then report recall by distance/density. This directly tests whether
  local suppressor templates make residual auditing artificially easy.
- **I11 (next evaluation): untouched external confirmation.** Freeze the wrapper,
  prompt renderer, and random seeds before collecting a new dataset/model family.
  This is required before treating the post-hoc safety gain as confirmatory.
- **I12 (adaptive audit): capture--recapture stopping.** Run two independent
  prompt-class samples and estimate unseen violation mass from witness overlap.
  Use the estimate only for calibrated abstention, never as a proof of
  monotonicity.

## 2026-09-20 — exposure-policy development (not confirmatory)

- **I13 (EWRA, failed development result).** After the unchanged standard
  enumeration prefix, score every unseen prompt class by the number of observed
  sufficient-subset and insufficient-superset relations that could yield an
  immediate witness. Balanced, raw-count, size-normalized, and maximin variants
  were declared before evaluation. All four collapsed to the same ordering and
  obtained .815 source-cluster mean raw-N recall over the pooled existing
  registry/news/all-active development corpus (571 clusters), below prompt-
  uniform .912 and shuffled-cover .913. EWRA--Uniform was -.096 with bootstrap
  95% interval [-.117,-.076]. This candidate is rejected, not promoted.
- **Failure diagnosis.** Selected classes almost always had exposure on only one
  side. Maximizing the number of comparable observations prioritized deep
  lattice states whose labels tended to agree with monotonicity, spending more
  queries (27.69 versus 24.49) and finding witnesses later (6.01 versus 3.98
  residual queries among detections).
- **I14 (predeclared second development panel).** Test (a) sparse exposure,
  which reverses the harmful depth preference; (b) nearest exposed cover edge;
  and (c) fixed 25/50/75% alternation between randomized cover-edge probes and
  global prompt-uniform probes. These policies may use only observed labels and
  prompt-class geometry. The full panel is logged regardless of outcome; no
  existing corpus is eligible as untouched confirmation afterward.
- **I14 result.** Sparse and nearest produced the same schedule on this corpus:
  .945 pooled N recall, +.033 [.021,.047] over prompt-uniform and +.032
  [.019,.045] over shuffled cover, with 23.12 total queries and 2.97 residual
  queries to a detected witness. Fixed 25/50/75 hybrids did not improve on
  Uniform. Because the gain is below the preregistered five-point threshold and
  one active NQ/Mistral cell is 4.2 points below Uniform, this is development
  evidence only. Nearest is the single frozen candidate for the untouched
  holdout because its cover-edge target matches the definition of N.
- **I15 (frozen untouched test).** Two no-collapse datasets (MSMARCO test and an
  unused NQ pool), two pinned 7B models, a new retrieved-instruction-conflict N
  mechanism, and at least 30 N sources per cell. Exact hashes and gates are in
  `NEAREST_HOLDOUT_FREEZE.md`.

### 2026-09-20 — Frozen holdout outcome and admissible next steps

- Confirmatory-I failed its prespecified sampling and performance gates.  The
  NQ2 cells yielded only 15 and 16 eligible N cases; pooled Nearest recall was
  0.835, with +0.038 over prompt-uniform and +0.028 over shuffled-cover.  The
  latter interval crossed zero and NQ2/Qwen was negative.
- Rejected: extending the revealed NQ2 pool, changing the budget, selecting a
  mixture weight from these four cells, or reporting only the significant
  prompt-uniform comparison.  Each would be optional stopping or post-hoc
  selection.
- A second test is admissible only as a separately declared Confirmatory-II on
  completely new sources/constructions, with the method and original gates
  unchanged, enough cases frozen up front, and multiplicity control across the
  two confirmatory attempts.  Confirmatory-I remains in the paper regardless of
  the outcome.
- Lower-risk paper direction: make the central contribution an audit/limits
  result—uniform's minimax property under hidden traps, the empirical absence of
  dynamic-only gains, and the blind failure of geometry-only ordering—rather
  than claim that Nearest is uniformly superior.

### 2026-09-20 — Confirmatory-II and post-submission research directions

- **I16 (frozen Confirmatory-II, in progress).** Use source-disjoint SQuAD and
  WebQuestions pools, a new scope-resolution surface form, deterministic full
  slot permutations, and a feasibility-only 40-source pilot before a sealed
  180-source final pool.  The construction is still honestly categorized as a
  broad suppressor/restorer Boolean family.  The second attempt uses one-sided
  97.5% bounds, two-baseline intersection--union testing, and an equal-attempt
  meta-analysis so its larger sample cannot erase Confirmatory-I's failure.
- **I16 result (prespecified STOP).** The feasibility-only pilot produced
  realized-N yields of 14/13 on SQuAD and 19/14 on WebQuestions for
  Qwen/Mistral, below the frozen 20-per-cell floor in all four cells.  There
  were zero request collisions and zero invalid oracle tables.  No method was
  evaluated, the sealed final pool remains untouched, and this construction is
  retired rather than tuned and retried.
- **I17 (future, not part of the frozen test): posterior witness-risk audit.**
  Replace a point-ranked next probe with a calibrated posterior over unseen
  comparable witness edges, trained only on development environments.  Evaluate
  both detection recall and calibration error; retain an explicit abstention
  outcome rather than turning the posterior into a completeness certificate.
- **I18 (future, naturalistic transfer): retrieval-originated ambiguity.** Mine
  naturally co-retrieved passages with entity or jurisdiction conflicts and
  have independent annotators specify whether a true suppressor/restorer
  relation exists.  This would test ecological validity missing from all-active
  synthetic constructions without weakening the present paper's claims.
- **I19 (future, sequential design): confidence-sequence budgeting.** Use an
  anytime-valid upper bound on unresolved witness mass to allocate queries while
  preserving optional-stopping validity.  Compare expected calls at fixed miss
  risk against the current fixed-budget audit; do not interpret the bound as a
  proof of global monotonicity.

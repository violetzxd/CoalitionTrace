# Independent review: reframing after prompt-equivalence accounting

Date: 2026-09-20  
Standard: ICASSP regular paper, realistic CCF-B review  
Scope: rapid independent review; no algorithm changes

## 1. Decision

The prompt-cached Mistral results end the method-superiority claim.  At budget 48,
AmbiCause reaches A ACEM 1.0 on both HotpotQA and NQ, but RandomMasks reaches .981
and RepeatedGreedy reaches .913/.931.  The improvements over RepeatedGreedy are
8.7 and 6.9 points, below the frozen 10-point threshold, while the advantage over
RandomMasks is only 1.9 points.  The earlier large query advantage was partly an
artifact of charging multiple masks that rendered to the same prompt.

Do not submit AmbiCause as a superior attribution algorithm.  A possible paper is:

> **Auditing Minimal-Cause Attribution in RAG: LOO Boundaries, Effective
> Intervention Dimension, and Non-Monotone Failure**

This must be a theory/benchmark/audit paper.  AmbiCause, repeated deletion and
random search become audited methods rather than the central contribution.  The
paper is potentially viable for ICASSP only if it demonstrates that the lessons
extend beyond this project's registry templates and self-created fixed slots.

Current readiness is **4/10 (weak reject)**.  It could reach borderline/weak
accept if the exact-query-space formalization, standard-enumerator results,
all-active control and stable-N evidence meet the falsifiable criteria below.

## 2. Prompt equivalence must be formalized correctly

Let `render(S)` be the exact token sequence submitted to the generator for mask
`S`.  Define

`S ~ T iff render(S) = render(T)`.

The real black-box intervention domain is the quotient

`Q = 2^D / ~`,

not the syntactic mask lattice `2^D`.  The generator cost of an exact cached
oracle is the number of queried equivalence classes.  Report:

- syntactic masks queried;
- unique rendered prompt hashes queried;
- input/output tokens and wall time;
- `|Q| / 2^n` and `log2 |Q|` as descriptive effective-domain measures;
- the number of slots for which observed and replacement text are identical.

`log2 |Q|` is not automatically a statistical dimension and should not be called
one without a theorem.  Use “effective intervention-domain size” or “effective
query dimension (descriptive)” and define it explicitly.

All methods must share a prompt-hash cache and a budget over unique rendered
prompts.  Ties caused by identical prompts are exact computation reuse, not
imputation.  Results using mask-count budgets may be retained only as an audit
showing how conclusions change under incorrect accounting.

### Critical novelty warning

In the present benchmark, prompt equivalence largely arises because noncausal
slots were deliberately set to `observed == replacement`.  A reviewer can fairly
call this an avoidable benchmark bug: those slots should either be removed from
the intervention universe or charged as one rendered context.

Therefore prompt equivalence alone is not a publishable contribution.  To elevate
it beyond a correction note, demonstrate at least one of the following:

1. the same overcounting occurs in two public context-attribution implementations
   or published benchmark protocols; or
2. naturally occurring equivalence/near-equivalence appears under chunking,
   padding, duplicated retrieval results or immutable context slots; or
3. a quotient-space formulation changes method ranking on an all-active control
   for reasons beyond literal identical slots.

If none holds, present prompt equivalence as a reproducibility lesson, not the
paper's headline novelty.

## 3. Defensible theoretical spine

The paper can contain three compact results:

1. **Unique monotone cause:** grand-coalition LOO exactly recovers the unique
   inclusion-minimal sufficient cause.
2. **Alternative monotone causes:** LOO returns exactly the intersection/backbone
   of all inclusion-minimal causes.
3. **Conditional enumeration:** exclusion-guided search enumerates all minimal
   causes only under monotonicity and frontier exhaustion.

These propositions are correct but elementary and adjacent to monotone
explanation/hitting-set literature.  They are insufficient alone for acceptance.
The empirical audit must carry substantial weight.

A stronger and relevant boundary is worth adding:

> With an unrestricted black-box Boolean utility, absence of a violation in a
> subexhaustive trace cannot certify global monotonicity; a non-monotone function
> can remain observationally indistinguishable on the queried masks.

State and prove the exact deterministic query lower bound only if it has been
checked carefully against property-testing literature.  At minimum, give an
indistinguishability proposition for the algorithm's observed trace.  Do not
claim a new general monotonicity-testing lower bound without a literature review.

This boundary explains the failed N detection more convincingly than presenting
another audit heuristic.

## 4. Paper narrative

The four-page story should be:

1. Minimal-cause RAG attribution is set-valued; independent scores are not the
   same as complete cause recovery.
2. Under monotonicity, LOO has an exact and underappreciated boundary: it solves U
   and returns only the common backbone on A.
3. Full-oracle U/A/N evaluation reveals two evaluation traps:
   syntactic-mask budgets can overcount identical interventions, and limited
   traces cannot safely certify non-monotonicity.
4. After correct prompt-level accounting, sophisticated and random/deletion
   enumeration methods are nearly tied on the current A benchmark, while N
   detection remains poor.

This is a useful negative/corrective result if reported without trying to rescue
AmbiCause as the winner.  The central empirical message is not “our enumerator is
best,” but “seemingly strong attribution gains can disappear after quotienting
the true intervention space, and completeness remains assumption-conditional.”

## 5. Minimum acceptable four-page experiment

### 5.1 Fully oracled core

Required cells:

- datasets: HotpotQA and Natural Questions;
- generators: Qwen2.5-7B-Instruct and Mistral-7B-Instruct-v0.3;
- one frozen registry family plus the frozen news wording family;
- `n=8` complete tables for every primary case;
- at least 40 independent source queries in each U/A/N
  dataset-generator cell, with exact source-level confidence intervals;
- at least 30 fully oracled `n=10` A cases per dataset-generator pair.

Report the complete screening funnel and realized cause structure.  For A, show
`|M(v)|`, cause sizes, overlap/backbone, cross-path recombination and construction
family.  A table dominated by two disjoint size-2 causes is not enough; at least
25% of A cases should contain a size-3 cause and both overlap bands must appear.

### 5.2 All-active control

Construct a control where every declared intervention slot has distinct observed
and replacement text, so `|Q|=2^n` unless accidental token identity occurs.  It
must preserve inertness without using fixed identical slots.  This control answers
whether near-ties arise because the causal search is genuinely easy or only
because the benchmark has a collapsed quotient space.

Run at least 30 A cases per dataset-generator pair.  If the method ranking changes
substantially, state that the original result is specific to collapsed prompt
spaces.  Do not average collapsed and all-active settings.

### 5.3 Methods

At identical unique-prompt budgets compare:

1. LOO/backbone;
2. RepeatedGreedy with ten frozen case-derived seeds;
3. RandomMasks with ten frozen case-derived seeds;
4. complement-based hierarchical deletion;
5. a standard hitting-set/minimal-explanation enumerator using the same cache and
   minimizer;
6. AmbiCause as the RAG adaptation;
7. exhaustive oracle, used only as truth and a cost ceiling.

KernelSHAP/ContextCite may be included if space permits, but the standard
enumerator is mandatory.  If it matches AmbiCause, say so and remove algorithmic
novelty language.

For stochastic algorithms, average within source over frozen seeds and bootstrap
source queries.  Seeds are not independent samples.  Report ACEM-budget curves,
not only budget 48.

### 5.4 N audit

Complete the frozen target-margin, second prompt-order and alternative-replacement
audits.  Define and report raw-N and stable-N separately.  For each method show:

- observed-violation recall;
- false alarm rate on U/A;
- unsafe conditional/unconditional completeness rate;
- selective risk versus coverage;
- fraction of all oracle violating edges actually queried.

The post-development upward audit remains exploratory.  It cannot replace the
failed confirmatory AmbiCause result.  A compact negative table is sufficient for
the paper; the full edge analysis can be in the artifact.

### 5.5 Accounting audit

For every primary cell, report results under:

- incorrect syntactic-mask accounting, clearly labeled retrospective;
- correct unique-prompt accounting;
- actual input/output token accounting.

Show how ACEM, method ranking and cost ratios change.  The comparison is paired on
the same cases and must not retune budgets after seeing the corrected results.

## 6. Statistics

- Source query is the independent unit.
- Use paired bootstrap with 10,000 source-level resamples for ACEM and call/token
  differences.
- Use McNemar exact tests only for a small predeclared binary comparison family;
  apply Holm correction.
- Report dataset/model/family cells separately before any stratified pooled
  estimate.
- For multi-seed methods, compute each source's expected score over frozen seeds
  first, then bootstrap sources.
- Report exact binomial intervals for N detection and unsafe-certificate rates.
- Do not run a superiority test between 1.000 and .981 and imply practical
  importance; the observed 1.9-point difference is below the frozen threshold.

## 7. Falsifiable acceptance criteria

This reframed paper should proceed only if all conditions below hold.

### Theory and ground truth

- Zero implementation violations of the LOO-backbone propositions on every
  monotone complete table.
- Independent oracle code reproduces U/A/N and `M(v)` on a random 10% sample.
- The monotonicity-certification claim is explicitly conditional, or a valid
  trace-indistinguishability/lower-bound result is supplied.

### Prompt-equivalence audit

- Correct prompt caching changes at least one substantive cost or ranking
  conclusion in both datasets and both generators; otherwise it is too local for
  a headline contribution.
- Unique-prompt counts and token costs are exactly reproducible from released
  hashes.
- The all-active control is reported.  If prompt equivalence disappears and all
  methods become trivial or conclusions reverse, the limitation is stated rather
  than pooled away.

### Benchmark breadth

- Both datasets, both generators and the held-out wording family show the same
  qualitative LOO U/A boundary.
- Each primary U/A/N cell has at least 40 independent sources; no source/template
  variant is counted twice.
- A includes nontrivial size-3 and overlapping causes, not only disjoint pairs.
- Stable-N contains at least 30 cases per dataset-generator pair; otherwise N is
  explicitly exploratory.

### Method audit

- Under prompt-level budgets, no method is advertised as superior unless it
  beats the strongest standard enumerator by at least 10 ACEM points with a
  paired interval excluding zero in every primary cell.
- If RandomMasks remains within two points of AmbiCause, the correct conclusion
  is that the current A task is saturated/easy.
- Unsafe unconditional completeness is zero.  Conditional completeness is
  labeled as such in every table and example.
- N detection below .80 or false alarm above .10 is reported as a failed safety
  mechanism, not reframed as success.

Failure of the method-superiority criteria does not kill the audit paper; it
determines its negative conclusion.  Failure of benchmark breadth, prompt-cache
reproducibility or stable-N validation does kill the ICASSP regular-paper claim.

## 8. Four-page allocation

- Page 1: problem, U/A/N definitions, LOO/backbone propositions and the prompt
  quotient definition.
- Page 2: benchmark/intervention design, accounting protocol and one compact
  algorithm/baseline description.
- Page 3: main table across dataset/model cells plus the mask-vs-prompt accounting
  figure.
- Page 4: A saturation, N failure/stable-N audit, limitations and conclusion.
- Page 5: references, ethics/compliance and allowed acknowledgments only.

Do not spend space presenting AmbiCause pseudocode as the main novelty.  Use that
space for the quotient-space correction and the N safety boundary.

## 9. Final recommendation

The reframe is viable but narrow.  It is stronger scientifically than continuing
to optimize an advantage that disappeared under correct accounting.  The paper's
value would be a reproducible warning about three conflated objects:

1. document masks;
2. distinct rendered interventions; and
3. minimal causes under an unverified monotonicity assumption.

At present, the result is a solid internal audit, not yet an ICASSP paper.  The
standard enumerator, all-active control, second family, stable-N audit and complete
four-cell prompt-cached analysis determine whether it crosses the publication
threshold.


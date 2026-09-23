# Uniform residual auditing under unknown witness locations

Status: proof draft created after the negative EWRA development result. It must
not be described as preregistered or confirmatory.

## Setup

After an unchanged cause-enumeration prefix, let `U` contain the `M` unqueried
rendered-prompt equivalence classes. Relative to the current closed trace, call
a class a *one-step witness class* when replaying it, propagating its value to
all equivalent masks, and checking comparable observed masks immediately yields
a sufficient-subset/insufficient-superset pair. Let exactly `K` classes in `U`
be witness classes. An audit pays for at most `b` distinct classes and stops at
the first witness.

This definition is trace-relative. It does not say that the remaining oracle is
fixed under arbitrary future observations, and it does not turn a miss into a
monotonicity certificate.

## Proposition (fixed-prefix uniform detection)

For any fixed initial one-step witness set `W`, with `|W|=K`, prompt-uniform
sampling without replacement of `b'=min(b,M)` distinct classes has detection
probability

`1 - choose(M-K, b') / choose(M, b')`,

with the numerator defined as zero when `b' > M-K`. A sequential audit that
queries `b'` classes unless it first finds a witness has detection probability
at least this value: querying a member of the initial `W` still exposes its
prefix witness, while earlier misses may create additional comparable pairs.

### Proof

The probability that a uniform `b'`-subset avoids the fixed `W` is

`(M-K)/M * (M-K-1)/(M-1) * ... * (M-K-b'+1)/(M-b'+1)`,

which equals `choose(M-K,b')/choose(M,b')`. Taking the complement proves the
formula; dynamic witnesses can only add detections.

## Corollary (conditional exchangeability of static hits)

Suppose that, conditional on the complete miss transcript--including every
observed utility label--the initial witness set remains exchangeable over the
remaining classes, and a miss supplies no information about its remaining
locations beyond excluding the queried class. Then every adaptive policy that
queries `b'` distinct classes unless it hits has the same probability of hitting
the *initial* witness set as uniform sampling above. Its total violation-
detection probability can be larger if miss observations create dynamic
witnesses, so the equality must not be applied to that broader event.

## Theorem (minimax hidden-witness guarantee)

For `0<=b<=M`, consider the following static hidden-target search game.  Exactly
`K` of the `M` classes are targets, querying a target is the only success event,
and every non-target query returns the same miss feedback; in particular, a
sequence of misses cannot create a new target.  All `K`-subsets are admissible.
No randomized adaptive policy with budget `b` can guarantee success probability
greater than

`V(M,K,b) = 1 - choose(M-K,b) / choose(M,b)`.

Uniform sampling without replacement attains `V(M,K,b)` for every `K`-subset of
target locations and is therefore minimax optimal in this static game.  The
single-target value is the special case `V(M,1,b)=b/M`.  This is an adversarial
static subproblem and a conservative rationale for uniform scheduling, not a
claim that uniform is globally minimax for a real sequential audit with dynamic
witness creation.

### Proof

Put the uniform distribution on the `choose(M,K)` possible witness sets.  Fix a
policy's internal randomness.  On the common all-miss path it selects a set `Q`
of at most `b` distinct classes.  A uniform hidden witness set avoids `Q` with
probability `choose(M-|Q|,K)/choose(M,K)`, so its detection probability is at
most `V(M,K,b)`.  Averaging over the policy randomness preserves that upper
bound.  Consequently at least one fixed witness set has detection probability
no larger than `V`; this is the usual averaging (or Yao) argument.  A uniform
`b`-subset avoids every fixed `K`-set with probability
`choose(M-K,b)/choose(M,b)`, which is the same quantity by the standard
hypergeometric identity.  It therefore attains the upper bound pointwise.

## Corollary (limits of geometry-only priority in the static game)

Any deterministic geometry-only ranking that queries a proper prefix (`b<M`)
has zero worst-case detection for every `K<=M-b`: the adversary places all
witnesses after the prefix while preserving the common all-miss transcript.
For `K=1`, a randomized geometry policy is minimax only if every class has
inclusion probability at least `b/M`; because the inclusion probabilities sum
to at most `b`, equality is necessary for every class.  This condition concerns
marginals and does not require the queried subset itself to be uniformly
distributed (a balanced block design can also satisfy it).  Thus, within this
static family, an unvalidated geometric score cannot improve the worst-case
guarantee by concentrating audit mass: any gain on favored locations is paid
for by a weaker location.

This is not a claim that geometry is useless under a distributional model.  It
states precisely what extra premise is required: a geometry-aware improvement
must be supported by a relationship between the score and witness location that
is learned independently of the evaluation family.

## Corollary (bounded-shortfall policy-level mixture)

Let `H` be any possibly randomized geometry-aware policy and let `0<=lambda<=1`.
Choose the complete uniform audit with probability `lambda` and `H` otherwise,
before observing labels.  The mixture detects every fixed `K`-witness instance
with probability at least `lambda V(M,K,b)`.  Its positive shortfall from the
uniform minimax benchmark, `[V-P_mix(W)]_+`, is therefore at most
`(1-lambda)V(M,K,b)`.  The bound is worst-case tight over unrestricted `H`, but
may be loose for a particular heuristic.  Any `lambda<1` deliberately gives up
part of uniform's worst-case floor in exchange for a possible gain from side
information; it is not a no-cost improvement.

### Proof

The mixture's success probability is `lambda V+(1-lambda)P_H`, and `P_H>=0`.
Subtracting the resulting lower bound from `V` and taking the positive part
gives the shortfall statement.

## Corollary (worst-case exhaustive requirement)

Fix a common monotone completion `f0` and `M` eligible unqueried classes. For
each eligible class `j`, let `f_j` change only that whole prompt class, leave the
queried trace unchanged, and make one member mask immediately oppose a
comparable observed mask. Any deterministic audit that guarantees detection
over `{f0,f_1,...,f_M}` must query all `M` classes in the worst case. If the
changed class is uniform, any randomized audit making at most `b` distinct
queries succeeds with probability at most `b/M`, attained by uniform sampling.

### Proof

For a deterministic audit that stops before querying all classes, select an
unqueried class and use its corresponding indistinguishable non-monotone
completion; the returned trace is identical to the monotone completion, so the
audit cannot soundly distinguish them. Under a uniformly hidden changed class,
condition on the audit's randomness and take its queried set on `f0`, which is
the common-miss path. Its set has size at most `b`, hence contains the changed
class with probability at most `b/M`. Averaging over the audit randomness keeps
the same upper bound (equivalently, Yao's principle). Uniform sampling attains
the bound for this one-trap family.

## Scope and empirical falsification route

- The result is about replay scheduling after the enumeration prefix, not cause
  enumeration or global monotonicity certification.
- No order is placed on prompt classes. Every subset comparison is between a
  class member mask and an observed mask in the Boolean lattice `2^D`.
- Exchangeability is a no-validated-side-information model. Lattice geometry
  can break it; a geometry-aware policy should therefore be evaluated on
  untouched mechanisms rather than justified from development gains alone.
- The EWRA development failure is consistent with this warning: exposure depth
  was side information, but it was negatively associated with realized witness
  labels. It does not prove that every structured policy must fail.
- Report the exact finite-population probability only when `M`, `K`, and the
  trace-relative witness definition are explicit. In deployment `K` is unknown,
  so the theorem supplies a minimax rationale, not a calibrated confidence that
  the oracle is monotone.
- With a fixed prefix, the finite-population formula can be checked offline by
  counting classes that individually yield a witness against that prefix. It is
  only a lower bound on a sequential audit when two classes that are
  individually harmless can jointly expose a reversal; any empirical excess
  must be reported rather than attributed to the fixed-witness model.

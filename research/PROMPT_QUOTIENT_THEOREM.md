# Exact replay accounting on the rendered-prompt quotient

Status: proof draft motivated by the prompt-accounting correction.  It is an
exact statement for deterministic decoding (or replay with fixed randomness),
not a claim about semantic near-duplicates.

## Setup

Let `X=2^D` be the finite mask domain, let `r:X->P` be the complete generator
request (rendered prompt together with fixed model revision, decoder/scorer
configuration, and any fixed randomness), and define `x~y` iff `r(x)=r(y)`
byte-for-byte.  The quotient classes are `Q=X/~`; write `m_q` for the number of
masks in class `q`, `N=|X|`, and `M=|Q|`.  Deterministic generation and scoring
give an oracle `v=h o r`, so `v` is constant on every class.

## Proposition 1 (lossless quotient simulation)

For every adaptive mask-query algorithm `A` whose decisions depend only on its
logical `(mask, oracle response)` transcript, there is a caching simulator
`A_Q` that returns exactly the same logical transcript and final output for
every oracle `v=h o r`, while making at most one physical generator call per
queried quotient class.  If `A` touches masks `x_1,...,x_T`, the number of
physical calls is exactly the number of distinct values among
`r(x_1),...,r(x_T)` and is at most `min(T,M)`.  No repeated query inside an
already observed class can reveal additional oracle information.  This simulates
the mask sequence that `A` would already have chosen; it does not claim that
reinvesting saved physical calls leaves `A`'s output unchanged.

### Proof

Maintain a dictionary keyed by the complete rendered prompt.  On a new key,
call the generator once and store the resulting oracle value; on a repeated key,
return the stored value.  Since `v(x)=h(r(x))`, every answer equals the answer
that an uncached run of `A` would receive.  Induction over the adaptive query
sequence therefore gives the same transcript and final output.  The call count
is the number of first occurrences of prompt keys.  Conditional on the stored
value, another mask in the same class is deterministic and supplies no new
oracle information.

## Proposition 2 (mask-uniform multiplicity bias)

If `b` distinct masks are sampled uniformly without replacement, the probability
of querying quotient class `q` at least once is

`pi_q(b) = 1 - choose(N-m_q,b)/choose(N,b)`,

with the numerator zero when `b>N-m_q`.  For `0<b<N`, `pi_q(b)` is
nondecreasing in `m_q` and is strictly increasing until it saturates at one
when `m_q>N-b`.  Hence mask-uniform sampling gives unequal intervention
coverage for classes of different sizes unless both are in this saturation
region.  With one draw,
`pi_q(1)=m_q/N`, so its class distribution is exactly size-biased.

### Proof

There are `choose(N,b)` mask samples and `choose(N-m_q,b)` that avoid all
members of `q`.  Taking the complement gives the expression.  Increasing
`m_q` strictly reduces the positive avoidance count; once fewer than `b`
nonmembers remain, avoidance is impossible and the hit probability is one.

## Corollary (hidden-class worst case)

In a static game with one violating quotient class, mask-uniform sampling has
worst-case detection

`min_q pi_q(b)`.

Under a budget of exactly `c<=M` distinct physical prompt-class calls, no
randomized policy can guarantee inclusion probability greater than `c/M` for an
unknown single violating class, because its marginal class-inclusion
probabilities sum to `c`.  Uniform class sampling makes every marginal `c/M`
and attains the bound.  Therefore a mask budget and a prompt-class budget are
not interchangeable: a small quotient class can receive much less audit
probability under fixed-count mask-uniform sampling, while a large duplicate
class can consume many logical mask draws without adding physical oracle
information.  The formula for `pi_q(b)` does not describe a different process
that continues drawing masks until it has accumulated `c` unique classes.

This comparison uses different natural budgets (`b` mask touches versus `c`
distinct physical replays).  A fair empirical comparison must report both and
must not silently set `b=c` when duplicates occur.

## Scope

- The equivalence is literal and includes the complete chat template and
  generation marker.  Approximate or semantic deduplication is not lossless.
- Fixed randomness can be included in the request key.  With fresh stochastic
  decoding, repeated prompts may estimate a response distribution and the
  no-new-information statement no longer applies.
- Algorithms that depend on latency, physical call counts, fresh randomness, or
  other generator side effects fall outside the transcript-only simulation.
- The quotient need not inherit a well-defined subset order: two masks in one
  prompt class may have different lattice relations to another mask.  Witness
  checks must propagate the queried class value back to every member mask.
- Proposition 2 diagnoses an evaluation and scheduling bias; it does not say
  that every size-weighted policy is suboptimal under every witness
  distribution.

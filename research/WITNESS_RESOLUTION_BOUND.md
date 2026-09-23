# Finite-population witness-resolution bound

Status: post-hoc theoretical extension.  This is a resolution guarantee for a
fixed-prefix witness set, not a monotonicity or cause-completeness certificate.

After an enumeration prefix, let `M` unqueried rendered-request classes remain.
Let `W` be the fixed set of `K` classes that, if individually replayed and
closed back to their member masks, would immediately expose a reversal against
the prefix.  Draw exactly `b<=M` distinct classes uniformly without replacement,
using design randomness independent of the unqueried oracle values.

For `0<alpha<1`, define

`K_U(M,b,alpha) = max { k : choose(M-k,b)/choose(M,b) >= alpha }`,

where the avoidance probability is zero when `M-k<b`.  If the audit observes
no witness, it may report `K_U` as a one-sided resolution bound.  Formally, for
every fixed oracle and fixed `K`,

`Pr(no initial-witness hit and K > K_U) <= alpha`.

This is an unconditional frequentist statement over the randomized audit
design.  It must not be paraphrased as a posterior probability that `K<=K_U`.

## Proof

Uniform sampling misses all `K` fixed witnesses with probability
`p_0(K)=choose(M-K,b)/choose(M,b)`, which is non-increasing in `K`.  By maximality
of `K_U`, every `K>K_U` has `p_0(K)<alpha` (or at most `alpha` under the adjacent
strict-threshold convention).  The claimed error event can occur only on this
zero-hit outcome.

## Prospective density-resolution design

For a prespecified witness-density threshold `rho`, set
`k_star=ceil(rho*M)` and choose the smallest integer `b` satisfying

`choose(M-k_star,b)/choose(M,b) <= alpha`.

Then any oracle having at least `k_star` initial one-step witness classes is
missed with probability at most `alpha`.  The values of `rho`, `alpha`, and `b`
must be fixed before observing audit labels; changing the budget in response to
misses requires a separate time-uniform construction.

## Scope

- The prefix may be adaptive, but the statement conditions on its realized
  trace.  The subsequent uniform permutation must be independent of unqueried
  utilities.
- If any initial or dynamically created witness is found, the audit rejects
  monotonicity and emits no zero-hit bound.  Dynamic hits can increase total
  detection, but are outside the hypergeometric equality.
- Small `K_U` does not imply approximate monotonicity: one rare witness can be
  important, and `K=0` does not exclude reversals revealed only by combinations
  of later observations.
- Per-case bounds have marginal coverage.  Simultaneous claims across cases
  require an explicit multiplicity correction.
- Exact class-uniform sampling currently requires rendering the small-`n`
  intervention domain.  The quotient supplies call identities, not a subset
  order; witness checks remain on member masks.

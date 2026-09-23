# When leave-one-out is sufficient

Let `v: 2^D -> {0,1}` be a Boolean sufficient-cause utility and assume `v` is
monotone with `v(D)=1`. Let `M(v)` denote the nonempty collection of
inclusion-minimal sufficient sets.

## Proposition 1 (unique-cause exactness)

If `M(v)={S*}`, then grand-coalition leave-one-out recovers `S*` exactly:

`i in S*` iff `v(D)-v(D\{i}) = 1`.

**Proof.** Every sufficient set contains an inclusion-minimal sufficient subset.
Uniqueness therefore implies every sufficient set contains `S*`.  For `i in S*`,
`D\{i}` cannot be sufficient.  For `j not in S*`, `D\{j}` still contains `S*`
and is sufficient by monotonicity.  The two LOO outcomes identify exactly the
members of `S*`.  QED.

## Proposition 2 (multiple-cause backbone)

Under the same monotonicity assumption, grand-coalition LOO returns exactly the
intersection of all inclusion-minimal sufficient causes:

`LOO(D) = intersection_{S in M(v)} S`.

For any element omitted by at least one minimal cause, removing that element from
`D` leaves that alternative cause intact; its LOO marginal is zero.  An element
present in every minimal cause cannot be removed while retaining sufficiency.

## Corollary (one-query ambiguity test)

Let `B=LOO(D)`. Under the same assumptions, `v(B)=1` if and only if `M(v)` has
exactly one member. Hence the full-set query, `n` grand-coalition deletions, and
one query of `B` both classify U versus A and recover the cause in U.

If `B` is sufficient, it contains some minimal cause `C`. Proposition 2 gives
`B subseteq C` because `B` is the intersection of all minimal causes, while
`C subseteq B` because `C` is contained in the sufficient set `B`. Thus `B=C`.
Every other minimal cause contains `B=C`, so minimality makes it equal to `C`.
The converse is Proposition 1. This is conditional on monotonicity and does not
certify the assumption.

## Consequence for CoalitionTrace

Interaction modeling is unnecessary in the unique monotone regime: `n+1` exact
replays solve the task.  It can only add value when the objective asks for causes
beyond the common backbone, or when utility is non-monotone/noisy.  Evaluation
must therefore stratify cases into:

- `U`: `v(empty)=0`, `v(D)=1`, monotone, with one inclusion-minimal cause;
- `A`: `v(empty)=0`, `v(D)=1`, monotone, with multiple alternative causes;
- `N`: `v(empty)=0`, `v(D)=1`, with a non-monotone cover edge.

The earlier claim that scalar LOO generally misses a unique strict coalition is
withdrawn.  Any future method must match the LOO fast path on `U` and justify its
extra queries through improved cause recovery on `A` or `N`.

## Proposition 3 (conditional completeness of exclusion enumeration)

Assume `v` is monotone and `v(D)=1`.  At a search node with exclusion set `E`,
query the maximal allowed set `D\E`.  If it is insufficient, no subset contained
in `D\E` is sufficient.  Otherwise minimize it to an inclusion-minimal cause
`C`.  For every `i in C`, create child `E union {i}`.  With an exact oracle,
deduplicated nodes and an unlimited budget, exhausting this tree returns exactly
`M(v)`.

**Proof.** Soundness follows because minimization returns a sufficient set whose
single-element deletions are insufficient; monotonicity then makes every proper
subset insufficient. For completeness, consider any undiscovered minimal cause
`C*` at a node that returned `C`. Since distinct inclusion-minimal causes cannot
contain one another, some `i in C` is absent from `C*`. Therefore `C*` remains
allowed in child `E union {i}`. Inductively, at least one unpruned descendant
retains `C*`. A node is pruned only when its maximal allowed set is insufficient;
monotonicity then rules out every cause in that node. Finite exhaustive traversal
must therefore discover `C*`. QED.

This is an assumption-conditional result.  A finite query trace that happens not
to contain a monotonicity violation does not prove the assumption, and the search
is closely related to established hitting-set/minimal-explanation enumeration.

## Proposition 4 (trace-level non-certifiability)

Let a partial black-box trace `T` over exact rendered-prompt equivalence classes
be consistent with at least one monotone Boolean completion. Suppose the entire
class represented by an unqueried mask `x` is absent from `T`, and `x` is
comparable to a queried mask in one
of the following ways:

1. some queried `y` strictly contains `x` and `v(y)=0`; or
2. some queried `z` is strictly contained in `x` and `v(z)=1`.

Then the trace is also consistent with a non-monotone completion. Consequently,
absence of an observed violating edge in such a trace cannot certify global
monotonicity.

**Proof.** Take any monotone completion consistent with `T`. In case 1,
monotonicity forces `v(x)=0`; change the value of the whole unqueried rendered-
prompt class of `x` to 1. The observed trace is unchanged, while `(x,y)` violates
monotonicity. In case 2, monotonicity forces `v(x)=1`; change the whole class to
0, leaving the trace unchanged and making `(z,x)` a violation. QED. The
class-level condition is necessary because deterministic replay assigns one
value to all masks rendering to the same prompt.

This is an observational indistinguishability statement for a realized trace,
not a claimed optimal lower bound for tolerant or distributional monotonicity
testing. It directly applies when a method has queried a sufficient cause but
leaves any of its supersets unqueried, as happened frequently in the N stress
tests.

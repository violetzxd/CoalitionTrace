from __future__ import annotations

from dataclasses import dataclass
import hashlib
import heapq
import math
import random

from .core import UtilityTable


@dataclass(frozen=True)
class CauseSetResult:
    causes: tuple[int, ...]
    queries: int
    complete_claim: bool = False
    observed_violation: tuple[int, int] | None = None
    enumeration_queries: int | None = None
    witness_audit_query: int | None = None
    quotient_exhausted: bool = False
    audit_trace: tuple[dict, ...] = ()


class _Cache:
    def __init__(self, table: UtilityTable, budget: int):
        self.table, self.budget = table, budget
        self.values: dict[int, float] = {}
        self.budget_hit = False
        self._violation: tuple[int, int] | None = None
        self.class_members: dict[str | int, list[int]] = {}
        for member in table.values:
            self.class_members.setdefault(table.query_key(member), []).append(member)

    def _observe(self, mask: int, value: float) -> None:
        """Close one observed prompt class over every equivalent lattice mask."""
        if mask in self.values:
            return
        if self._violation is None:
            if value >= self.table.tau:
                for upper, upper_value in self.values.items():
                    if upper_value < self.table.tau and mask & upper == mask:
                        self._violation = (mask, upper)
                        break
            else:
                for lower, lower_value in self.values.items():
                    if lower_value >= self.table.tau and lower & mask == lower:
                        self._violation = (lower, mask)
                        break
        self.values[mask] = value

    def sufficient(self, mask: int) -> bool | None:
        if mask not in self.values:
            if not self.table.can_query(mask, self.budget):
                self.budget_hit = True
                return None
            value = self.table.query(mask)
            key = self.table.query_key(mask)
            for member in self.class_members[key]:
                # Byte-identical deterministic prompts share the queried value.
                # Never inspect the unqueried member's stored oracle outcome.
                self._observe(member, value)
        return self.values[mask] >= self.table.tau

    @property
    def queries(self) -> int:
        return self.table.unique_queries

    def violation(self) -> tuple[int, int] | None:
        """Return any observed sufficient-subset/insufficient-superset pair."""
        return self._violation


def _balanced_minimize(cache: _Cache, allowed: int) -> int | None:
    """Standard balanced deletion minimizer for a monotone sufficient set."""
    if cache.sufficient(allowed) is not True:
        return None
    current = allowed
    granularity = 2
    while current.bit_count() >= 2:
        bits = [i for i in range(cache.table.n) if current & (1 << i)]
        chunk_size = math.ceil(len(bits) / granularity)
        reduced = False
        for start in range(0, len(bits), chunk_size):
            candidate = current
            for i in bits[start:start + chunk_size]:
                candidate &= ~(1 << i)
            state = cache.sufficient(candidate)
            if state is None:
                return None
            if state:
                current = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if not reduced:
            if granularity >= len(bits):
                break
            granularity = min(len(bits), granularity * 2)
    for i in range(cache.table.n):
        bit = 1 << i
        if not current & bit:
            continue
        state = cache.sufficient(current & ~bit)
        if state is None:
            return None
        if state:
            current &= ~bit
    for i in range(cache.table.n):
        if current & (1 << i) and cache.sufficient(current & ~(1 << i)) is not False:
            return None
    return current


def _enumerate_with_cache(cache: _Cache) -> tuple[set[int], bool]:
    table = cache.table
    full = (1 << table.n) - 1
    frontier: list[tuple[int, int]] = [(0, 0)]
    seen = {0}
    causes: set[int] = set()
    exhausted = True
    while frontier:
        _, excluded = heapq.heappop(frontier)
        cause = _balanced_minimize(cache, full & ~excluded)
        if cause is None:
            if cache.budget_hit:
                exhausted = False
                break
            continue
        causes.add(cause)
        bits = cause
        while bits:
            bit = bits & -bits
            child = excluded | bit
            if child not in seen:
                seen.add(child)
                heapq.heappush(frontier, (child.bit_count(), child))
            bits -= bit
    return causes, exhausted


def standard_monotone_enumerator(table: UtilityTable, budget: int) -> CauseSetResult:
    """Reference exclusion/hitting-set enumeration with balanced minimization.

    This intentionally omits the LOO-backbone fast path.  It is the strongest
    task-matched baseline for assessing whether that RAG-specific adaptation adds
    anything beyond established monotone minimal-explanation enumeration.
    """
    cache = _Cache(table, budget)
    causes, exhausted = _enumerate_with_cache(cache)
    violation = cache.violation()
    quotient_exhausted = cache.queries == len({table.query_key(m) for m in table.values})
    return CauseSetResult(tuple(sorted(causes)), cache.queries,
                          exhausted and violation is None, violation,
                          cache.queries, 0 if violation else None,
                          quotient_exhausted)


def residual_audited_enumerator(
    table: UtilityTable,
    budget: int,
    *,
    mode: str = "bidirectional",
    seed: int | None = None,
) -> CauseSetResult:
    """Enumerate first, then audit with the same residual prompt budget."""
    supported = {
        "bidirectional", "upward", "downward", "random",
        "exposed_random", "exposure_balanced", "exposure_raw",
        "exposure_normalized", "exposure_maximin", "exposure_sparse",
        "exposure_nearest", "hybrid_25", "hybrid_50", "hybrid_75",
    }
    if mode not in supported:
        raise ValueError(f"Unknown residual audit mode: {mode}")
    cache = _Cache(table, budget)
    causes, exhausted = _enumerate_with_cache(cache)
    enumeration_queries = cache.queries
    full = (1 << table.n) - 1
    violation = cache.violation()
    witness_audit_query = 0 if violation is not None else None
    rng = random.Random(seed)
    audit_trace: list[dict] = []
    while violation is None:
        candidates: set[int] = set()
        class_candidates: dict[str | int, list[int]] = {}
        if mode in {
            "random", "exposed_random", "exposure_balanced", "exposure_raw",
            "exposure_normalized", "exposure_maximin", "exposure_sparse",
            "exposure_nearest", "hybrid_25", "hybrid_50", "hybrid_75",
        }:
            # Sample physical interventions rather than syntactic masks: keep one
            # representative for each prompt-equivalence class not yet replayed.
            for key, members in cache.class_members.items():
                if not table.was_queried(members[0]):
                    class_candidates[key] = members
            candidates.update(members[0] for members in class_candidates.values())
        else:
            for mask, value in tuple(cache.values.items()):
                if value >= table.tau and mode in {"bidirectional", "upward"}:
                    remaining = full & ~mask
                    while remaining:
                        bit = remaining & -remaining
                        if mask | bit not in cache.values:
                            candidates.add(mask | bit)
                        remaining -= bit
                elif value < table.tau and mode in {"bidirectional", "downward"}:
                    remaining = mask
                    while remaining:
                        bit = remaining & -remaining
                        if mask & ~bit not in cache.values:
                            candidates.add(mask & ~bit)
                        remaining -= bit
        if not candidates:
            break
        score_by_mask: dict[int, tuple[float, float, float]] = {}
        exposure_mode = (
            mode.startswith("exposure_") or mode == "exposed_random"
            or mode.startswith("hybrid_")
        )
        if exposure_mode:
            observed_one = [m for m, v in cache.values.items() if v >= table.tau]
            observed_zero = [m for m, v in cache.values.items() if v < table.tau]
            for key, members in class_candidates.items():
                e1 = sum(
                    1 for member in members for upper in observed_zero
                    if member != upper and member & upper == member
                )
                e0 = sum(
                    1 for lower in observed_one for member in members
                    if lower != member and lower & member == lower
                )
                size = len(members)
                balanced = float(e0 > 0) + float(e1 > 0)
                normalized = (e0 + e1) / size
                min_normalized = min(e0, e1) / size
                distances = [
                    (member ^ upper).bit_count()
                    for member in members for upper in observed_zero
                    if member != upper and member & upper == member
                ] + [
                    (lower ^ member).bit_count()
                    for lower in observed_one for member in members
                    if lower != member and lower & member == lower
                ]
                min_distance = min(distances) if distances else table.n + 1
                representative = members[0]
                if mode == "exposure_balanced":
                    score_by_mask[representative] = (balanced, normalized, min_normalized)
                elif mode == "exposure_raw":
                    score_by_mask[representative] = (float(e0 + e1), balanced, min_normalized)
                elif mode == "exposure_normalized":
                    score_by_mask[representative] = (normalized, balanced, min_normalized)
                elif mode == "exposure_maximin":
                    score_by_mask[representative] = (float(min(e0, e1)), balanced, normalized)
                elif mode == "exposure_sparse":
                    score_by_mask[representative] = (balanced, -normalized, -float(min_distance))
                elif mode == "exposure_nearest":
                    score_by_mask[representative] = (balanced, -float(min_distance), -normalized)
                else:
                    score_by_mask[representative] = (
                        balanced, -float(min_distance), -normalized
                    )
        if mode == "exposed_random":
            exposed = [m for m in candidates if score_by_mask[m][0] > 0]
            ordered = exposed or list(candidates)
            rng.shuffle(ordered)
        elif mode.startswith("hybrid_"):
            boundary_fraction = int(mode.rsplit("_", 1)[1]) / 100.0
            audit_index = cache.queries - enumeration_queries
            cycle_position = (audit_index + (seed or 0)) % 4
            boundary_slots = round(4 * boundary_fraction)
            boundary = [
                m for m in candidates
                if score_by_mask[m][0] > 0 and score_by_mask[m][1] == -1.0
            ]
            pool = boundary if cycle_position < boundary_slots and boundary else list(candidates)
            ordered = sorted(
                pool,
                key=lambda m: hashlib.sha256(
                    f"{seed}:{cache.queries - enumeration_queries}:{table.query_key(m)}".encode()
                ).hexdigest(),
                reverse=True,
            )
        elif mode.startswith("exposure_"):
            def ranked(mask: int) -> tuple:
                key = table.query_key(mask)
                digest = hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()
                return (*score_by_mask[mask], digest)
            ordered = sorted(candidates, key=ranked, reverse=True)
        else:
            ordered = sorted(candidates, key=lambda m: (m.bit_count(), m))
            if seed is not None:
                rng.shuffle(ordered)
        progressed = False
        for mask in ordered:
            before = len(cache.values)
            selected_score = score_by_mask.get(mask)
            selected_key = str(table.query_key(mask))
            if cache.sufficient(mask) is None:
                quotient_exhausted = cache.queries == len(
                    {table.query_key(m) for m in table.values}
                )
                return CauseSetResult(
                    tuple(sorted(causes)), cache.queries, False,
                    cache.violation(), enumeration_queries, witness_audit_query,
                    quotient_exhausted, tuple(audit_trace),
                )
            progressed |= len(cache.values) > before
            violation = cache.violation()
            audit_trace.append({
                "query": cache.queries - enumeration_queries,
                "key_sha256": hashlib.sha256(selected_key.encode()).hexdigest(),
                "score": selected_score,
                "witness": violation is not None,
            })
            if violation is not None:
                witness_audit_query = cache.queries - enumeration_queries
                break
            if exposure_mode:
                # Scores are trace-dependent; recompute after every new class.
                break
        if not progressed:
            break
    quotient_exhausted = cache.queries == len({table.query_key(m) for m in table.values})
    return CauseSetResult(
        tuple(sorted(causes)), cache.queries,
        exhausted and violation is None, violation,
        enumeration_queries, witness_audit_query, quotient_exhausted,
        tuple(audit_trace),
    )


def safety_audited_enumerator(table: UtilityTable, budget: int) -> CauseSetResult:
    """Deterministic bidirectional cover-boundary audit."""
    return residual_audited_enumerator(table, budget, mode="bidirectional")


def upward_audited_enumerator(table: UtilityTable, budget: int) -> CauseSetResult:
    return residual_audited_enumerator(table, budget, mode="upward")


def downward_audited_enumerator(table: UtilityTable, budget: int) -> CauseSetResult:
    return residual_audited_enumerator(table, budget, mode="downward")


def random_residual_audited_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0,
) -> CauseSetResult:
    return residual_audited_enumerator(table, budget, mode="random", seed=seed)


def shuffled_safety_audited_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0,
) -> CauseSetResult:
    return residual_audited_enumerator(
        table, budget, mode="bidirectional", seed=seed,
    )


def exposure_weighted_audited_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0, variant: str = "balanced",
) -> CauseSetResult:
    return residual_audited_enumerator(
        table, budget, mode=f"exposure_{variant}", seed=seed,
    )


def exposed_random_audited_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0,
) -> CauseSetResult:
    return residual_audited_enumerator(
        table, budget, mode="exposed_random", seed=seed,
    )


def hybrid_residual_audited_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0, boundary_percent: int = 50,
) -> CauseSetResult:
    if boundary_percent not in {25, 50, 75}:
        raise ValueError("boundary_percent must be 25, 50, or 75")
    return residual_audited_enumerator(
        table, budget, mode=f"hybrid_{boundary_percent}", seed=seed,
    )


def loo_set(table: UtilityTable, budget: int) -> CauseSetResult:
    cache = _Cache(table, budget)
    full = (1 << table.n) - 1
    if cache.sufficient(full) is not True:
        return CauseSetResult((), cache.queries)
    backbone = 0
    for i in range(table.n):
        state = cache.sufficient(full & ~(1 << i))
        if state is None:
            return CauseSetResult((), cache.queries)
        if not state:
            backbone |= 1 << i
    if cache.sufficient(backbone) is not True:
        return CauseSetResult((), cache.queries)
    for i in range(table.n):
        if backbone & (1 << i) and cache.sufficient(backbone & ~(1 << i)) is not False:
            return CauseSetResult((), cache.queries)
    return CauseSetResult((backbone,), cache.queries, True)


def repeated_greedy(
    table: UtilityTable, budget: int, *, seed: int = 0, orders: int = 10,
) -> CauseSetResult:
    """Enumerate causes discovered by independent random deletion orders."""
    cache = _Cache(table, budget)
    rng = random.Random(seed)
    full = (1 << table.n) - 1
    causes: set[int] = set()
    for _ in range(orders):
        if cache.sufficient(full) is not True:
            break
        order = list(range(table.n))
        rng.shuffle(order)
        current = full
        for i in order:
            state = cache.sufficient(current & ~(1 << i))
            if state is None:
                return CauseSetResult(tuple(sorted(causes)), cache.queries)
            if state:
                current &= ~(1 << i)
        # Under monotonicity, deletion minimality is inclusion minimality.  The
        # baseline makes no global completeness claim.
        if all(cache.sufficient(current & ~(1 << i)) is False
               for i in range(table.n) if current & (1 << i)):
            causes.add(current)
    return CauseSetResult(tuple(sorted(causes)), cache.queries)


def random_mask_enumerator(
    table: UtilityTable, budget: int, *, seed: int = 0,
) -> CauseSetResult:
    """Uniform-mask baseline with exact cached minimality checks when affordable."""
    cache = _Cache(table, budget)
    rng = random.Random(seed)
    masks = list(range(1 << table.n))
    rng.shuffle(masks)
    candidates: set[int] = set()
    for mask in masks:
        if cache.queries >= budget and not cache.table.was_queried(mask):
            break
        if cache.sufficient(mask) is not True:
            continue
        minimal = True
        affordable = True
        # Stream proper subsets and stop at the first witness.  Materializing and
        # replaying every subset is needlessly exponential when a small
        # sufficient witness already disproves minimality.
        for sub in range(mask):
            if sub & mask != sub:
                continue
            state = cache.sufficient(sub)
            if state is None:
                affordable = False
                break
            if state:
                minimal = False
                break
        if minimal and affordable:
            candidates.add(mask)
        if not affordable:
            break
    return CauseSetResult(tuple(sorted(candidates)), cache.queries)

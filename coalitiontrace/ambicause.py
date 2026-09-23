from __future__ import annotations

from dataclasses import dataclass
import heapq
import math

from .core import UtilityTable


@dataclass(frozen=True)
class AmbiCauseResult:
    """Budget-qualified set-valued attribution result.

    ``complete`` is a global certificate only when ``mode`` is ``monotone`` and
    the exclusion frontier was exhausted.  A result never infers monotonicity
    from finitely many probes.
    """

    causes: tuple[int, ...]
    backbone: int
    queries: int
    mode: str
    complete: bool
    observed_violation: tuple[int, int] | None


class _Oracle:
    def __init__(self, table: UtilityTable, budget: int):
        self.table = table
        self.budget = int(budget)
        self.cache: dict[int, float] = {}
        self.budget_hit = False

    def ask(self, mask: int) -> float | None:
        if mask in self.cache:
            return self.cache[mask]
        if not self.table.can_query(mask, self.budget):
            self.budget_hit = True
            return None
        value = self.table.query(mask)
        self.cache[mask] = value
        return value

    def sufficient(self, mask: int) -> bool | None:
        value = self.ask(mask)
        return None if value is None else value >= self.table.tau

    def violation(self) -> tuple[int, int] | None:
        """Return an observed sufficient-subset/insufficient-superset pair."""
        sufficient = [m for m, v in self.cache.items() if v >= self.table.tau]
        insufficient = [m for m, v in self.cache.items() if v < self.table.tau]
        for lower in sufficient:
            for upper in insufficient:
                if lower & upper == lower:
                    return lower, upper
        return None


def _minimalize(oracle: _Oracle, allowed: int, fixed: int = 0) -> int | None:
    """Balanced chunk deletion followed by replay-verified 1-minimal checks."""
    status = oracle.sufficient(allowed)
    if status is not True:
        return None
    current = allowed
    granularity = 2
    while (current & ~fixed).bit_count() >= 2:
        bits = [i for i in range(oracle.table.n)
                if current & (1 << i) and not fixed & (1 << i)]
        chunk_size = math.ceil(len(bits) / granularity)
        reduced = False
        for start in range(0, len(bits), chunk_size):
            candidate = current
            for i in bits[start:start + chunk_size]:
                candidate &= ~(1 << i)
            state = oracle.sufficient(candidate)
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
    for i in range(oracle.table.n):
        bit = 1 << i
        if not current & bit or fixed & bit:
            continue
        candidate = current & ~bit
        status = oracle.sufficient(candidate)
        if status is None:
            return None
        if status:
            current = candidate
    # A second pass makes the result independent of non-monotone deletion order
    # with respect to the declared 1-minimality condition.
    for i in range(oracle.table.n):
        bit = 1 << i
        if current & bit:
            status = oracle.sufficient(current & ~bit)
            if status is None or status:
                return None
    return current


def _general_search(oracle: _Oracle) -> tuple[set[int], bool]:
    """Cardinality-first search with no monotone pruning.

    Causes added at a given cardinality are exact inclusion minima because every
    smaller mask has already been processed.  Global completeness requires the
    whole lattice to be exhausted.
    """
    known: set[int] = set()
    for mask in sorted(range(1 << oracle.table.n), key=lambda m: (m.bit_count(), m)):
        if mask not in oracle.cache and not oracle.table.can_query(mask, oracle.budget):
            return known, False
        status = oracle.sufficient(mask)
        if status is not True:
            continue
        if not any(cause & mask == cause for cause in known):
            known.add(mask)
    return known, True


def _audit_upward_edges(oracle: _Oracle, cause: int) -> tuple[int, int] | None:
    """Test cover edges immediately above a verified sufficient cause."""
    full = (1 << oracle.table.n) - 1
    remaining = full & ~cause
    while remaining:
        bit = remaining & -remaining
        state = oracle.sufficient(cause | bit)
        if state is None:
            return None
        if not state:
            return cause, cause | bit
        remaining -= bit
    return None


def ambicause(
    table: UtilityTable,
    budget: int,
    *,
    assume_monotone: bool = True,
    general_fallback: bool = True,
    audit_upward: bool = False,
) -> AmbiCauseResult:
    """LOO fast path plus exclusion-guided all-minimal-cause enumeration.

    Under a monotone Boolean utility and sufficient budget, the exclusion tree is
    complete: after finding cause C, every different minimal cause omits at least
    one non-backbone member of C and therefore occurs in a corresponding child.
    Query caching makes the accounting use unique generator replays.
    """
    oracle = _Oracle(table, budget)
    full = (1 << table.n) - 1
    if oracle.sufficient(full) is not True:
        return AmbiCauseResult((), 0, table.unique_queries, "conditional-monotone",
                               True, None)

    backbone = 0
    for i in range(table.n):
        status = oracle.sufficient(full & ~(1 << i))
        if status is None:
            return AmbiCauseResult((), backbone, table.unique_queries, "budget", False,
                                   oracle.violation())
        if not status:
            backbone |= 1 << i

    known: set[int] = set()
    # If the LOO backbone itself is sufficient, Proposition 2 makes it the sole
    # minimal cause under monotonicity; direct minimality replays validate output.
    candidate = _minimalize(oracle, backbone, fixed=backbone)
    if candidate is not None:
        known.add(candidate)
        if audit_upward:
            found = _audit_upward_edges(oracle, candidate)
            if found is not None:
                return AmbiCauseResult(tuple(sorted(known)), backbone,
                                       table.unique_queries, "nonmonotone", False, found)
        violation = oracle.violation()
        if violation is None and assume_monotone:
            return AmbiCauseResult(tuple(sorted(known)), backbone, table.unique_queries,
                                   "conditional-monotone", True, None)

    # Priority favors fewer exclusions (large balanced search regions).  A node
    # denotes all causes contained in D\excluded and containing the LOO backbone.
    frontier: list[tuple[int, int]] = [(0, 0)]
    seen_exclusions = {0}
    exhausted = True
    while frontier:
        _, excluded = heapq.heappop(frontier)
        allowed = full & ~excluded
        if backbone & ~allowed:
            continue
        cause = _minimalize(oracle, allowed, fixed=backbone)
        if oracle.violation() is not None:
            exhausted = False
            break
        if cause is None:
            if oracle.budget_hit:
                exhausted = False
                break
            continue
        known.add(cause)
        if audit_upward and _audit_upward_edges(oracle, cause) is not None:
            exhausted = False
            break
        branch_bits = cause & ~backbone
        while branch_bits:
            bit = branch_bits & -branch_bits
            child = excluded | bit
            if child not in seen_exclusions:
                seen_exclusions.add(child)
                heapq.heappush(frontier, (child.bit_count(), child))
            branch_bits -= bit

    violation = oracle.violation()
    mode = "nonmonotone" if violation is not None else "conditional-monotone"
    complete = bool(assume_monotone and violation is None and exhausted)
    if general_fallback and (violation is not None or not assume_monotone):
        known, complete = _general_search(oracle)
        violation = oracle.violation()
        mode = "nonmonotone" if violation is not None else "general"
    return AmbiCauseResult(tuple(sorted(known)), backbone, table.unique_queries, mode,
                           complete, violation)

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
import random

import numpy as np
from sklearn.linear_model import Ridge

from .core import UtilityTable


@dataclass(frozen=True)
class BaselineResult:
    mask: int | None
    verified_1_minimal: bool
    queries: int


def _ask(table: UtilityTable, queried: dict[int, float], mask: int, budget: int) -> bool:
    """Populate ``queried[mask]`` if its prompt-equivalence class is affordable."""
    if mask in queried:
        return True
    if not table.can_query(mask, budget):
        return False
    queried[mask] = table.query(mask)
    return True


def _verify(table: UtilityTable, queried: dict[int, float], mask: int, budget: int):
    _ask(table, queried, mask, budget)
    if queried.get(mask, 0.0) < table.tau:
        return False
    parents = [mask & ~(1 << i) for i in range(table.n) if mask & (1 << i)]
    for parent in parents:
        _ask(table, queried, parent, budget)
    return all(parent in queried and queried[parent] < table.tau for parent in parents)


def greedy_deletion(table: UtilityTable, budget: int) -> BaselineResult:
    queried: dict[int, float] = {}
    mask = (1 << table.n) - 1
    if not _ask(table, queried, mask, budget):
        return BaselineResult(None, False, table.unique_queries)
    if queried[mask] < table.tau:
        return BaselineResult(None, False, table.unique_queries)
    changed = True
    while changed:
        changed = False
        for i in range(table.n):
            if not mask & (1 << i):
                continue
            candidate = mask & ~(1 << i)
            if not _ask(table, queried, candidate, budget):
                break
            if queried[candidate] >= table.tau:
                mask, changed = candidate, True
                break
    valid = _verify(table, queried, mask, budget)
    return BaselineResult(mask if valid else None, valid, table.unique_queries)


def ddmin(table: UtilityTable, budget: int) -> BaselineResult:
    """Classic complement-based delta debugging followed by real 1-minimal checks."""
    queried: dict[int, float] = {}
    current = (1 << table.n) - 1
    if not _ask(table, queried, current, budget):
        return BaselineResult(None, False, table.unique_queries)
    if queried[current] < table.tau:
        return BaselineResult(None, False, table.unique_queries)
    granularity = 2
    while current.bit_count() >= 2:
        bits = [i for i in range(table.n) if current & (1 << i)]
        chunk_size = math.ceil(len(bits) / granularity)
        reduced = False
        for start in range(0, len(bits), chunk_size):
            chunk = bits[start:start + chunk_size]
            complement = current
            for bit in chunk:
                complement &= ~(1 << bit)
            if not _ask(table, queried, complement, budget):
                break
            if queried[complement] >= table.tau:
                current = complement
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if not reduced:
            if granularity >= len(bits):
                break
            granularity = min(len(bits), granularity * 2)
    valid = _verify(table, queried, current, budget)
    return BaselineResult(current if valid else None, valid, table.unique_queries)


def loo_rank(table: UtilityTable, budget: int) -> BaselineResult:
    queried: dict[int, float] = {}
    full = (1 << table.n) - 1
    if not _ask(table, queried, full, budget):
        return BaselineResult(None, False, table.unique_queries)
    scores = []
    for i in range(table.n):
        mask = full & ~(1 << i)
        if not _ask(table, queried, mask, budget):
            break
        scores.append((queried[full] - queried[mask], i))
    selected = 0
    for _, i in sorted(scores, reverse=True):
        selected |= 1 << i
        _ask(table, queried, selected, budget)
        if queried.get(selected, 0.0) >= table.tau and _verify(table, queried, selected, budget):
            return BaselineResult(selected, True, table.unique_queries)
    return BaselineResult(None, False, table.unique_queries)


def kernel_shap_attributions(table: UtilityTable, budget: int, seed: int = 0):
    """Constrained KernelSHAP coefficients and queried-value cache.

    Empty/full endpoints are exact constraints, so local accuracy is numerical,
    not an approximation induced by an arbitrary large endpoint weight.
    """
    rng = random.Random(seed)
    queried: dict[int, float] = {}
    full = (1 << table.n) - 1
    by_size = {size: [] for size in range(1, table.n)}
    for mask in range(1, full):
        by_size[mask.bit_count()].append(mask)
    for masks in by_size.values():
        rng.shuffle(masks)
    pool = []
    while any(by_size.values()):
        for size in range(1, table.n):
            if by_size[size]:
                pool.append(by_size[size].pop())
    # Prompt-equivalent masks are free after the first rendered-prompt replay, so
    # continue through the pool until the next novel prompt would exceed budget.
    sample = [0, full] + pool
    for mask in sample:
        if not table.can_query(mask, budget):
            break
        queried[mask] = table.query(mask)
    interior = [mask for mask in queried if mask not in (0, full)]
    x = np.asarray([[(m >> i) & 1 for i in range(table.n)] for m in interior], float)
    y = np.asarray([queried[m] - queried[0] for m in interior], float)
    weights = []
    for mask in interior:
        size = mask.bit_count()
        weights.append((table.n - 1) /
                       (math.comb(table.n, size) * size * (table.n - size)))
    delta = queried[full] - queried[0]
    if interior:
        w = np.asarray(weights)
        gram = x.T @ (w[:, None] * x) + 1e-10 * np.eye(table.n)
        rhs = x.T @ (w * y)
        constraint = np.ones((table.n, 1))
        kkt = np.block([[gram, constraint], [constraint.T, np.zeros((1, 1))]])
        solution = np.linalg.solve(kkt, np.r_[rhs, delta])
        coef = solution[:table.n]
    else:
        coef = np.full(table.n, delta / table.n)
    assert np.isclose(coef.sum(), delta, atol=1e-7)
    return coef, queried


def kernel_shap(table: UtilityTable, budget: int, seed: int = 0) -> BaselineResult:
    """KernelSHAP ranking converted to one replay-verified minimal cause."""
    fit_budget = max(2, budget - table.n)
    coef, queried = kernel_shap_attributions(table, fit_budget, seed)
    selected = 0
    for i in np.argsort(-coef):
        selected |= 1 << int(i)
        _ask(table, queried, selected, budget)
        if queried.get(selected, 0.0) >= table.tau and _verify(table, queried, selected, budget):
            return BaselineResult(selected, True, table.unique_queries)
    return BaselineResult(None, False, table.unique_queries)


def random_search(table: UtilityTable, budget: int, max_size: int = 2, seed: int = 0):
    rng = random.Random(seed)
    pool = [
        sum(1 << i for i in idx)
        for size in range(1, max_size + 1)
        for idx in combinations(range(table.n), size)
    ]
    rng.shuffle(pool)
    queried: dict[int, float] = {}
    for mask in pool:
        if not table.can_query(mask, budget):
            break
        queried[mask] = table.query(mask)
        if queried[mask] >= table.tau and _verify(table, queried, mask, budget):
            return BaselineResult(mask, True, table.unique_queries)
    return BaselineResult(None, False, table.unique_queries)

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
import random
from typing import Iterable

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge

from .core import UtilityTable, masks_of_size


def _design(masks: Iterable[int], n: int, pairwise: bool = True) -> np.ndarray:
    masks = list(masks)
    main = np.asarray([[(m >> i) & 1 for i in range(n)] for m in masks], dtype=float)
    if not pairwise:
        return main
    pairs = np.asarray(
        [[row[i] * row[j] for i, j in combinations(range(n), 2)] for row in main],
        dtype=float,
    )
    return np.concatenate([main, pairs], axis=1)


class _Surrogate:
    def __init__(self, n: int, pairwise: bool, seed: int):
        self.n, self.pairwise, self.seed = n, pairwise, seed
        self.model = None
        self.constant = 0.0

    def fit(self, masks: list[int], y: list[float]) -> "_Surrogate":
        self.constant = float(np.mean(y)) if y else 0.0
        if len(set(y)) >= 2:
            self.model = LogisticRegression(
                penalty="l1", solver="liblinear", C=1.0, random_state=self.seed,
                max_iter=2000,
            ).fit(_design(masks, self.n, self.pairwise), np.asarray(y) >= 0.5)
        elif len(y) >= 3:
            self.model = Ridge(alpha=1.0).fit(_design(masks, self.n, self.pairwise), y)
        return self

    def predict(self, masks: list[int]) -> np.ndarray:
        if self.model is None:
            return np.full(len(masks), self.constant)
        x = _design(masks, self.n, self.pairwise)
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(x)[:, 1]
        return np.clip(self.model.predict(x), 0.0, 1.0)


def _bootstrap_predictions(
    masks: list[int], y: list[float], candidates: list[int], n: int,
    pairwise: bool, seed: int, bootstraps: int = 12,
) -> tuple[np.ndarray, np.ndarray]:
    base = _Surrogate(n, pairwise, seed).fit(masks, y).predict(candidates)
    if len(masks) < 4:
        return base, np.full(len(candidates), 0.25)
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(bootstraps):
        idx = rng.integers(0, len(masks), len(masks))
        bm = [masks[i] for i in idx]
        by = [y[i] for i in idx]
        rows.append(_Surrogate(n, pairwise, seed + b + 1).fit(bm, by).predict(candidates))
    return base, np.std(np.stack(rows), axis=0)


@dataclass(frozen=True)
class CoalitionTraceResult:
    mask: int | None
    verified_1_minimal: bool
    queries: int
    history: tuple[tuple[int, float], ...]


def coalition_trace(
    table: UtilityTable,
    budget: int,
    max_size: int = 2,
    pairwise: bool = True,
    active: bool = True,
    seed: int = 0,
) -> CoalitionTraceResult:
    """Budgeted candidate search; every returned set is verified by real table queries."""
    rng = random.Random(seed)
    queried: dict[int, float] = {}

    def ask(mask: int) -> float | None:
        if mask in queried:
            return queried[mask]
        if len(queried) >= budget:
            return None
        queried[mask] = table.query(mask)
        return queried[mask]

    full = (1 << table.n) - 1
    for mask in (0, full):
        ask(mask)
    # Size-one probes prevent the algorithm from fabricating a coalition for r=1.
    singleton_order = list(masks_of_size(table.n, 1))
    rng.shuffle(singleton_order)
    for mask in singleton_order[: max(1, min(table.n, budget // 4))]:
        ask(mask)

    # Diverse group probes are essential for pure interactions: a surrogate fitted
    # only to singletons cannot identify a zero-main-effect pair.
    probe_target = min(max(2, budget // 4), max(0, budget - len(queried)))
    group_pool = [
        m for m in range(1, 1 << table.n)
        if 2 <= m.bit_count() <= max(2, table.n - 1) and m not in queried
    ]
    rng.shuffle(group_pool)
    group_pool.sort(key=lambda m: abs(m.bit_count() - table.n / 2))
    for mask in group_pool[:probe_target]:
        ask(mask)

    candidates = [
        mask for size in range(1, max_size + 1) for mask in masks_of_size(table.n, size)
    ]

    while len(queried) < budget:
        sufficient = [
            m for m, v in queried.items()
            if v >= table.tau and m.bit_count() <= max_size
        ]
        verified = []
        for mask in sorted(sufficient, key=lambda m: (m.bit_count(), m)):
            parents = [mask & ~(1 << i) for i in range(table.n) if mask & (1 << i)]
            for parent in parents:
                ask(parent)
            if all(parent in queried and queried[parent] < table.tau for parent in parents):
                verified.append(mask)
        if verified:
            best = min(verified, key=lambda m: (m.bit_count(), m))
            # Continue if an unqueried smaller candidate remains; otherwise the best
            # is globally minimal within the declared max_size search space.
            if not any(m not in queried and m.bit_count() < best.bit_count() for m in candidates):
                return CoalitionTraceResult(
                    best, True, len(queried), tuple(sorted(queried.items()))
                )

        unqueried_candidates = [m for m in candidates if m not in queried]
        unqueried_probes = [m for m in group_pool if m not in queried]
        if not unqueried_candidates and not unqueried_probes:
            break
        masks, y = list(queried), list(queried.values())
        candidate_mean, _ = _bootstrap_predictions(
            masks, y, unqueried_candidates, table.n, pairwise, seed + len(queried)
        ) if unqueried_candidates else (np.asarray([]), np.asarray([]))
        plausible = [i for i, value in enumerate(candidate_mean) if value >= 0.5]
        if active and plausible:
            index = max(plausible, key=lambda i: (candidate_mean[i], -unqueried_candidates[i].bit_count()))
            next_mask = unqueried_candidates[index]
        elif active and unqueried_probes:
            mean, uncertainty = _bootstrap_predictions(
                masks, y, unqueried_probes, table.n, pairwise, seed + len(queried)
            )
            score = uncertainty + 0.5 * (1.0 - np.abs(mean - 0.5))
            index = max(range(len(unqueried_probes)), key=lambda i: score[i])
            next_mask = unqueried_probes[index]
        else:
            pool = unqueried_candidates or unqueried_probes
            next_mask = pool[rng.randrange(len(pool))]
        ask(next_mask)

    sufficient = [
        m for m, v in queried.items()
        if v >= table.tau and m.bit_count() <= max_size
    ]
    for mask in sorted(sufficient, key=lambda m: (m.bit_count(), m)):
        parents = [mask & ~(1 << i) for i in range(table.n) if mask & (1 << i)]
        if all(queried.get(parent, math.inf) < table.tau for parent in parents):
            return CoalitionTraceResult(mask, True, len(queried), tuple(sorted(queried.items())))
    return CoalitionTraceResult(None, False, len(queried), tuple(sorted(queried.items())))

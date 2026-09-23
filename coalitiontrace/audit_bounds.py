"""Exact finite-population bounds for prompt-uniform residual auditing."""

from __future__ import annotations

import math


def zero_hit_probability(population: int, witnesses: int, draws: int) -> float:
    """Probability of zero witnesses in uniform sampling without replacement."""
    if population < 0:
        raise ValueError("population must be non-negative")
    if not 0 <= witnesses <= population:
        raise ValueError("witnesses must lie in [0, population]")
    if not 0 <= draws <= population:
        raise ValueError("draws must lie in [0, population]")
    if draws > population - witnesses:
        return 0.0
    return math.comb(population - witnesses, draws) / math.comb(population, draws)


def zero_hit_upper_bound(population: int, draws: int, alpha: float = 0.05) -> int:
    """One-sided exact upper confidence bound after observing zero witnesses.

    Returns the largest witness count K whose probability of producing zero
    hits is at least ``alpha``.  Used as ``U(0)`` with the trivial bound
    ``U(x)=population`` for any positive hit count, this has coverage at least
    ``1-alpha`` for every fixed finite population and witness set.
    """
    if population < 0:
        raise ValueError("population must be non-negative")
    if not 0 <= draws <= population:
        raise ValueError("draws must lie in [0, population]")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")

    # The zero-hit probability is non-increasing in K.  Binary search for the
    # largest K that is not rejected by a zero-hit observation.
    low, high = 0, population
    while low < high:
        middle = (low + high + 1) // 2
        if zero_hit_probability(population, middle, draws) >= alpha:
            low = middle
        else:
            high = middle - 1
    return low


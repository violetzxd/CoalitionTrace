import itertools

import pytest

from coalitiontrace.audit_bounds import (
    zero_hit_probability,
    zero_hit_upper_bound,
)


def test_zero_hit_probability_matches_exhaustive_sampling():
    for population in range(1, 10):
        universe = range(population)
        for witnesses in range(population + 1):
            witness_set = set(range(witnesses))
            for draws in range(population + 1):
                samples = list(itertools.combinations(universe, draws))
                empirical = sum(
                    not witness_set.intersection(sample) for sample in samples
                ) / len(samples)
                assert empirical == pytest.approx(
                    zero_hit_probability(population, witnesses, draws)
                )


def test_zero_hit_bound_has_exact_finite_population_coverage():
    for population in range(1, 20):
        for draws in range(population + 1):
            for alpha in (0.01, 0.05, 0.1, 0.25):
                upper = zero_hit_upper_bound(population, draws, alpha)
                for witnesses in range(population + 1):
                    failure_probability = (
                        zero_hit_probability(population, witnesses, draws)
                        if witnesses > upper else 0.0
                    )
                    assert failure_probability <= alpha + 1e-15


@pytest.mark.parametrize(
    "population,draws,alpha,expected",
    [(100, 0, 0.05, 100), (100, 100, 0.05, 0), (10, 5, 0.05, 3)],
)
def test_known_bounds(population, draws, alpha, expected):
    assert zero_hit_upper_bound(population, draws, alpha) == expected


def test_invalid_arguments_are_rejected():
    with pytest.raises(ValueError):
        zero_hit_upper_bound(10, 11)
    with pytest.raises(ValueError):
        zero_hit_upper_bound(10, 5, 0)
    with pytest.raises(ValueError):
        zero_hit_probability(10, -1, 5)

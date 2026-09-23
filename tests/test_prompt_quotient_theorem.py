import itertools
import math

import pytest


def _hit_probability(total: int, class_size: int, draws: int) -> float:
    if draws > total - class_size:
        return 1.0
    return 1.0 - math.comb(total - class_size, draws) / math.comb(total, draws)


def test_mask_uniform_class_hit_formula_matches_exhaustive_counting():
    for total in range(1, 9):
        masks = range(total)
        for class_size in range(1, total + 1):
            target = set(range(class_size))
            for draws in range(total + 1):
                samples = list(itertools.combinations(masks, draws))
                observed = sum(bool(target.intersection(s)) for s in samples) / len(samples)
                assert observed == pytest.approx(
                    _hit_probability(total, class_size, draws)
                )


def test_class_hit_probability_is_monotone_and_strict_before_saturation():
    for total in range(2, 20):
        for draws in range(1, total):
            probabilities = [
                _hit_probability(total, class_size, draws)
                for class_size in range(1, total + 1)
            ]
            assert all(a <= b for a, b in zip(probabilities, probabilities[1:]))
            for class_size, (a, b) in enumerate(
                zip(probabilities, probabilities[1:]), start=1
            ):
                if class_size <= total - draws:
                    assert a < b
                else:
                    assert a == b == 1.0


def test_uniform_class_sampling_balances_physical_budget_marginals():
    for classes in range(1, 9):
        universe = range(classes)
        for calls in range(classes + 1):
            schedules = list(itertools.combinations(universe, calls))
            marginals = [
                sum(q in schedule for schedule in schedules) / len(schedules)
                for q in universe
            ]
            assert sum(marginals) == pytest.approx(calls)
            assert all(p == pytest.approx(calls / classes) for p in marginals)

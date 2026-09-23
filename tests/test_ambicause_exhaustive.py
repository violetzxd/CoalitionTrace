from itertools import combinations

from coalitiontrace.ambicause import ambicause
from coalitiontrace.core import UtilityTable


def _antichains(n: int):
    masks = range(1, 1 << n)
    for width in range(1, len(masks) + 1):
        for family in combinations(masks, width):
            if all(not (a & b == a or a & b == b)
                   for i, a in enumerate(family) for b in family[i + 1:]):
                yield family


def test_ambicause_complete_for_every_nonempty_monotone_n4_function():
    # Every monotone Boolean function is uniquely represented by its antichain of
    # minimal true masks. Exhausting all n=4 antichains tests the theorem and code.
    checked = 0
    for truth in _antichains(4):
        table = UtilityTable(4, {
            mask: float(any(mask & cause == cause for cause in truth))
            for mask in range(16)
        })
        result = ambicause(table, budget=16, general_fallback=False)
        assert set(result.causes) == set(truth)
        assert result.complete
        checked += 1
    assert checked == 166  # M(4)=168, excluding constant-zero and constant-one.

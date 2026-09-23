from coalitiontrace.core import UtilityTable


def test_inclusion_minima_for_nonmonotone_skip_level_case():
    # 001 is sufficient, 011 is not, 111 is sufficient: immediate-deletion-only
    # validation of 111 would be wrong because 001 is a sufficient proper subset.
    table = UtilityTable(3, {m: float(m in {0b001, 0b101, 0b111}) for m in range(8)})
    assert table.inclusion_minima() == (0b001,)
    assert not table.is_monotone()

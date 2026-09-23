from scripts.paired_statistics import holm_adjust


def test_holm_adjust_preserves_order_and_step_down_monotonicity() -> None:
    adjusted = holm_adjust([0.04, 0.01, 0.03, 0.50])
    assert adjusted == [0.09, 0.04, 0.09, 0.50]


def test_holm_adjust_handles_empty_family() -> None:
    assert holm_adjust([]) == []

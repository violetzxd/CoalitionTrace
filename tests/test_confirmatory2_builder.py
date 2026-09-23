import hashlib

from coalitiontrace.benchmark_confirmatory2 import make_confirmatory2_case
from coalitiontrace.core import build_prompt


ROW = {
    "id": "squad:test-source",
    "question": "Who wrote the example novel?",
    "correct": "Ada Example",
    "target": "Grace Sample",
}


def test_confirmatory2_cases_are_all_active_and_have_256_distinct_requests():
    for stratum in ("U", "A", "N"):
        case = make_confirmatory2_case(ROW, stratum)
        assert case.n == 8
        assert all(a != b for a, b in zip(case.observed, case.replacements))
        hashes = {
            hashlib.sha256("\n".join(build_prompt(case, mask)).encode()).hexdigest()
            for mask in range(1 << case.n)
        }
        assert len(hashes) == 256


def test_n_variants_are_distinct_and_place_scope_shift_before_restoration():
    first = make_confirmatory2_case(ROW, "N", variant=0)
    second = make_confirmatory2_case(ROW, "N", variant=1)
    first_shift = next(i for i, text in enumerate(first.observed)
                       if "Ada Example" in text)
    first_restore = next(i for i, text in enumerate(first.observed)
                         if "Grace Sample" in text and "ruling" in text)
    second_shift = next(i for i, text in enumerate(second.observed)
                        if "Ada Example" in text)
    second_restore = next(i for i, text in enumerate(second.observed)
                          if "Grace Sample" in text and "addendum" in text)
    assert (first_shift, first_restore) != (second_shift, second_restore)
    assert first_restore in first.planted_causes[0]


def test_generation_is_deterministic():
    assert make_confirmatory2_case(ROW, "N", variant=1).to_json() == (
        make_confirmatory2_case(ROW, "N", variant=1).to_json()
    )


def test_frozen_slot_permutation_uses_every_position_without_fixed_low_bits():
    role_positions = {"shift": [], "restore": []}
    for source in range(128):
        row = dict(ROW, id=f"squad:balance-{source}")
        case = make_confirmatory2_case(row, "N", variant=source % 2)
        role_positions["shift"].append(next(
            i for i, text in enumerate(case.observed) if "Ada Example" in text
        ))
        role_positions["restore"].append(next(
            i for i, text in enumerate(case.observed)
            if "Grace Sample" in text and ("ruling" in text or "addendum" in text)
        ))
    for positions in role_positions.values():
        counts = [positions.count(index) for index in range(8)]
        assert min(counts) >= 7
        assert max(counts) - min(counts) <= 16

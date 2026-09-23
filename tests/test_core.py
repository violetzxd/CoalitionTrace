from coalitiontrace.baselines import (
    ddmin, greedy_deletion, kernel_shap, kernel_shap_attributions,
)
from coalitiontrace.ambicause import ambicause
from coalitiontrace.set_baselines import (
    _Cache, exposure_weighted_audited_enumerator,
    hybrid_residual_audited_enumerator, loo_set,
    random_residual_audited_enumerator, repeated_greedy,
    safety_audited_enumerator, standard_monotone_enumerator,
)
from coalitiontrace.core import CoalitionCase, UtilityTable, build_prompt, extract_short_answer
from coalitiontrace.benchmark_uan import make_uan_case
from coalitiontrace.benchmark_holdout import make_holdout_case
from coalitiontrace.search import coalition_trace
from scripts.make_audit_variants import permute, replace_neutral


def pair_table(n=6):
    truth = (1 << 1) | (1 << 4)
    return UtilityTable(n, {m: float((m & truth) == truth) for m in range(1 << n)})


def test_slot_preserving_prompt():
    case = CoalitionCase("x", "bridge", "q", "c", "t", ("A", "B"), ("a", "b"), (0, 1))
    _, empty = build_prompt(case, 0)
    _, full = build_prompt(case, 3)
    assert "[Passage 1]" in empty and "[Passage 2]" in empty
    assert len(empty.split("[Passage")) == len(full.split("[Passage"))
    assert "a" in empty and "A" in full


def test_format_only_short_answer_extraction():
    assert extract_short_answer("Answer: Joan Baez (according to Passage 2)") == "Joan Baez"
    assert extract_short_answer("UNKNOWN (the passages do not answer this)\nMore") == "UNKNOWN"


def test_oracle_minima_and_validity():
    table = pair_table()
    truth = (1 << 1) | (1 << 4)
    assert table.oracle_minima() == (truth,)
    assert table.strict_minimal(truth)
    assert table.inclusion_minima() == (truth,)
    assert table.is_monotone()
    assert table.loo_backbone() == truth


def test_loo_backbone_is_intersection_of_alternative_causes():
    first, second = 0b0011, 0b1100
    table = UtilityTable(4, {
        mask: float((mask & first) == first or (mask & second) == second)
        for mask in range(16)
    })
    assert set(table.inclusion_minima()) == {first, second}
    assert table.loo_backbone() == 0


def test_backbone_query_exactly_decides_unique_monotone_cause_exhaustively():
    """Exhaust all Boolean utilities on three items satisfying the theorem."""
    n = 3
    full = (1 << n) - 1
    for truth_table in range(1 << (1 << n)):
        values = {
            mask: float(bool(truth_table & (1 << mask)))
            for mask in range(1 << n)
        }
        if not values[full]:
            continue
        monotone = all(
            not values[lower] or values[upper]
            for lower in range(1 << n)
            for upper in range(1 << n)
            if lower & upper == lower
        )
        if not monotone:
            continue
        table = UtilityTable(n, values)
        minima = table.inclusion_minima()
        backbone = table.loo_backbone()
        assert bool(values[backbone]) == (len(minima) == 1)
        if len(minima) == 1:
            assert backbone == minima[0]
    assert table.is_monotone()


def test_coalition_trace_finds_pure_pair():
    table = pair_table()
    result = coalition_trace(table, budget=32, max_size=2, seed=3)
    assert result.mask == (1 << 1) | (1 << 4)
    assert result.verified_1_minimal


def test_ddmin_is_valid_but_not_budget_free():
    table = pair_table()
    result = ddmin(table, budget=20)
    assert result.verified_1_minimal
    assert result.queries > 1


def test_kernel_shap_is_budget_accounted():
    table = pair_table()
    result = kernel_shap(table, budget=32, seed=4)
    assert result.queries <= 32


def test_kernel_shap_local_accuracy_and_known_additive_values():
    weights = (0.2, -0.4, 0.7)
    table = UtilityTable(3, {
        mask: 0.1 + sum(weight for i, weight in enumerate(weights) if mask & (1 << i))
        for mask in range(8)
    }, tau=10.0)
    phi, queried = kernel_shap_attributions(table, budget=8, seed=0)
    assert len(queried) == 8
    assert tuple(phi.round(6)) == weights
    assert abs(phi.sum() - (table.values[7] - table.values[0])) < 1e-8


def test_prompt_equivalent_masks_share_generator_replay_cost():
    # Bit 1 is a fixed slot: toggling it leaves the rendered prompt unchanged.
    table = UtilityTable(
        2,
        {mask: float(bool(mask & 0b01)) for mask in range(4)},
        query_keys={mask: mask & 0b01 for mask in range(4)},
    )
    table.query(0b11)
    table.query(0b01)
    assert table.unique_masks == 2
    assert table.unique_queries == 1
    assert table.can_query(0b00, budget=2)
    table.query(0b00)
    assert table.unique_queries == 2
    assert table.can_query(0b10, budget=2)


def test_greedy_deletion_remains_separate_baseline():
    result = greedy_deletion(pair_table(), budget=20)
    assert result.verified_1_minimal


def test_ambicause_unique_uses_loo_fast_path():
    table = pair_table()
    result = ambicause(table, budget=20)
    assert result.causes == table.inclusion_minima()
    assert result.backbone == table.loo_backbone()
    assert result.complete and result.mode == "conditional-monotone"


def test_ambicause_enumerates_disjoint_and_overlapping_causes():
    causes = (0b00011, 0b01100, 0b10101)
    table = UtilityTable(5, {
        mask: float(any(mask & cause == cause for cause in causes))
        for mask in range(1 << 5)
    })
    result = ambicause(table, budget=1 << 5)
    assert set(result.causes) == set(causes)
    assert result.complete


def test_ambicause_flags_observed_nonmonotonicity():
    # {0} is sufficient, adding item 1 suppresses it; {2,3} is another cause.
    values = {
        mask: float(((mask & 0b0001) and not (mask & 0b0010))
                    or (mask & 0b1100) == 0b1100)
        for mask in range(16)
    }
    table = UtilityTable(4, values)
    result = ambicause(table, budget=16, assume_monotone=False)
    assert result.mode == "nonmonotone"
    assert result.observed_violation is not None
    assert set(result.causes) == set(table.inclusion_minima())


def test_upward_audit_detects_suppressor_above_unique_cause():
    values = {mask: float((mask & 0b0001) and not (mask & 0b0010))
              for mask in range(16)}
    # Keep the full context sufficient while preserving the suppressor edge.
    values[0b1111] = 1.0
    table = UtilityTable(4, values)
    result = ambicause(table, budget=32, audit_upward=True,
                       general_fallback=False)
    assert result.mode == "nonmonotone"
    assert result.observed_violation is not None


def test_uan_builder_randomizes_and_roundtrips():
    row = {
        "id": "source-1", "question": "Who won?", "correct": "Alice",
        "target": "Bob", "documents": [{"text": f"background {i}"} for i in range(12)],
    }
    case = make_uan_case(row, "A", cause_size=2, overlap=False, n=8)
    restored = CoalitionCase.from_json(case.to_json())
    assert restored == case
    assert len(case.planted_causes) == 2
    assert all(len(cause) == 2 for cause in case.planted_causes)
    assert case.poison_indices != (0, 1, 2, 3)


def test_all_active_builder_has_distinct_rendered_prompts():
    row = {
        "id": "source-active", "question": "Who won?", "correct": "Alice",
        "target": "Bob", "documents": [{"text": f"background {i}"} for i in range(12)],
    }
    case = make_uan_case(row, "A", cause_size=2, n=8, all_active=True)
    prompts = {build_prompt(case, mask) for mask in range(1 << case.n)}
    assert len(prompts) == 1 << case.n
    assert all(observed != replacement for observed, replacement
               in zip(case.observed, case.replacements))


def test_holdout_builder_has_distinct_prompts_and_new_n_mechanism():
    row = {
        "id": "holdout-source", "question": "Who won?", "correct": "Alice",
        "target": "Bob", "documents": [{"text": "Neutral sports archive."}],
    }
    case = make_holdout_case(row, "N", cause_size=2, n=8)
    prompts = {build_prompt(case, mask) for mask in range(1 << case.n)}
    assert len(prompts) == 1 << case.n
    assert any("UNTRUSTED RETRIEVED INSTRUCTION" in doc for doc in case.observed)
    assert any("Retrieval integrity policy" in doc for doc in case.observed)


def test_audit_variants_preserve_slot_and_cause_invariants():
    row = {
        "id": "source-audit", "question": "Who won?", "correct": "Alice",
        "target": "Bob", "documents": [{"text": f"background {i}"} for i in range(12)],
    }
    case = make_uan_case(row, "N", cause_size=2, n=8)
    ordered = permute(case)
    alternative = replace_neutral(case)
    assert sorted(ordered.observed) == sorted(case.observed)
    assert len(ordered.poison_indices) == len(case.poison_indices)
    assert alternative.observed == case.observed
    assert alternative.replacements != case.replacements


def test_set_baselines_do_not_claim_all_causes_on_ambiguous_table():
    causes = (0b0011, 0b1100)
    table = UtilityTable(4, {m: float(any(m & c == c for c in causes)) for m in range(16)})
    assert loo_set(table.fork(), 16).causes == ()
    greedy = repeated_greedy(table.fork(), 16, seed=2, orders=10)
    assert set(greedy.causes).issubset(set(causes))
    assert not greedy.complete_claim


def test_standard_monotone_enumerator_recovers_all_causes():
    causes = (0b0011, 0b1100)
    table = UtilityTable(4, {m: float(any(m & c == c for c in causes)) for m in range(16)})
    result = standard_monotone_enumerator(table, budget=16)
    assert set(result.causes) == set(causes)
    assert result.complete_claim


def test_safety_audit_preserves_monotone_enumeration():
    causes = (0b0011, 0b1100)
    values = {m: float(any(m & c == c for c in causes)) for m in range(16)}
    standard = standard_monotone_enumerator(UtilityTable(4, values), budget=16)
    audited = safety_audited_enumerator(UtilityTable(4, values), budget=16)
    assert audited.causes == standard.causes
    assert audited.observed_violation is None
    assert audited.queries <= 16


def test_safety_audit_detects_suppressor_after_enumeration():
    values = {mask: float((mask & 0b0001) and not (mask & 0b0010))
              for mask in range(16)}
    values[0b1111] = 1.0
    audited = safety_audited_enumerator(UtilityTable(4, values), budget=16)
    assert audited.observed_violation is not None
    lower, upper = audited.observed_violation
    assert lower & upper == lower
    assert values[lower] == 1.0 and values[upper] == 0.0


def test_safety_audit_matches_standard_prefix_across_budgets():
    cause_sets = [(0b0001,), (0b0011, 0b1100), (0b0011, 0b0101, 0b1001)]
    for causes in cause_sets:
        values = {m: float(any(m & c == c for c in causes)) for m in range(16)}
        for budget in range(1, 17):
            standard = standard_monotone_enumerator(UtilityTable(4, values), budget)
            audited = safety_audited_enumerator(UtilityTable(4, values), budget)
            ewra = exposure_weighted_audited_enumerator(
                UtilityTable(4, values), budget, seed=0,
            )
            assert audited.causes == standard.causes
            assert ewra.causes == standard.causes
            assert audited.enumeration_queries == standard.queries
            assert ewra.enumeration_queries == standard.queries
            assert audited.queries <= budget
            assert ewra.queries <= budget


def test_residual_audits_return_sound_witnesses_with_prompt_collisions():
    values = {mask: float((mask & 0b0001) and not (mask & 0b0010))
              for mask in range(16)}
    values[0b1111] = 1.0
    query_keys = {
        mask: (mask & 0b0111, mask if mask in {0b0111, 0b1111} else None)
        for mask in values
    }
    for seed in range(5):
        result = random_residual_audited_enumerator(
            UtilityTable(4, values, query_keys=query_keys), budget=8, seed=seed,
        )
        assert result.queries <= 8
        if result.observed_violation:
            lower, upper = result.observed_violation
            assert lower & upper == lower
            assert values[lower] == 1.0 and values[upper] == 0.0


def test_prompt_class_closure_exposes_zero_cost_lattice_witness():
    values = {mask: 0.0 for mask in range(8)}
    values[0b011] = values[0b100] = 1.0
    query_keys = {mask: mask for mask in values}
    query_keys[0b011] = query_keys[0b100] = "sufficient-class"
    cache = _Cache(UtilityTable(3, values, query_keys=query_keys), budget=2)
    assert cache.sufficient(0b011) is True
    assert cache.sufficient(0b110) is False
    assert cache.queries == 2
    assert cache.violation() == (0b100, 0b110)


def test_ewra_next_class_is_blind_to_unqueried_labels():
    cause = 0b0011
    values = {m: float(m & cause == cause) for m in range(16)}
    prefix_table = UtilityTable(4, values)
    prefix = standard_monotone_enumerator(prefix_table, budget=16)
    queried = set(prefix_table.queries)
    altered = dict(values)
    for mask in altered:
        if mask not in queried:
            altered[mask] = 1.0 - altered[mask]
    budget = prefix.queries + 1
    first = exposure_weighted_audited_enumerator(
        UtilityTable(4, values), budget, seed=7,
    )
    second = exposure_weighted_audited_enumerator(
        UtilityTable(4, altered), budget, seed=7,
    )
    assert first.enumeration_queries == second.enumeration_queries == prefix.queries
    assert first.audit_trace[0]["key_sha256"] == second.audit_trace[0]["key_sha256"]


def test_all_adaptive_audits_are_blind_to_unqueried_labels():
    cause = 0b0011
    values = {m: float(m & cause == cause) for m in range(16)}
    prefix_table = UtilityTable(4, values)
    prefix = standard_monotone_enumerator(prefix_table, budget=16)
    queried = set(prefix_table.queries)
    altered = {m: (v if m in queried else 1.0 - v) for m, v in values.items()}
    budget = prefix.queries + 1
    runners = [
        lambda t: exposure_weighted_audited_enumerator(
            t, budget, seed=11, variant="sparse"),
        lambda t: exposure_weighted_audited_enumerator(
            t, budget, seed=11, variant="nearest"),
        lambda t: hybrid_residual_audited_enumerator(
            t, budget, seed=11, boundary_percent=25),
        lambda t: hybrid_residual_audited_enumerator(
            t, budget, seed=11, boundary_percent=50),
        lambda t: hybrid_residual_audited_enumerator(
            t, budget, seed=11, boundary_percent=75),
    ]
    for runner in runners:
        first = runner(UtilityTable(4, values))
        second = runner(UtilityTable(4, altered))
        assert first.audit_trace[0]["key_sha256"] == second.audit_trace[0]["key_sha256"]


def test_ewra_variants_never_exceed_budget_and_return_sound_witnesses():
    values = {
        mask: float((mask & 0b0001) and not (mask & 0b0010))
        for mask in range(16)
    }
    values[0b1111] = 1.0
    for variant in ("balanced", "sparse", "nearest"):
        result = exposure_weighted_audited_enumerator(
            UtilityTable(4, values), budget=12, seed=3, variant=variant,
        )
        assert result.queries <= 12
        if result.observed_violation:
            lower, upper = result.observed_violation
            assert lower & upper == lower
            assert values[lower] == 1.0 and values[upper] == 0.0

from __future__ import annotations

import numpy as np
import pytest

from scripts.confirmatory2_statistics import base_clusters, combined_meta


def _row(dataset: str, model: str, source: str, method: str,
         seed: int, detected: float) -> dict:
    return {
        "dataset": dataset, "model": model, "source_id": source,
        "case_id": f"{dataset}:{source}", "stratum": "N", "budget": 48,
        "method": method, "seed": seed, "detected_nonmonotone": detected,
    }


def test_seed_then_model_averaging_prevents_pseudoreplication() -> None:
    rows = []
    for model, nearest in (("qwen", (1.0, 0.0)), ("mistral", (1.0, 1.0))):
        for seed, value in enumerate(nearest):
            rows.append(_row("squad", model, "s1", "EWRA-Nearest", seed, value))
            rows.append(_row("squad", model, "s1", "RandomResidualAudit", seed, 0.0))
            rows.append(_row("squad", model, "s1", "ShuffledSafeAudit", seed, 0.0))
    clusters = base_clusters(rows)
    assert set(clusters) == {("squad", "s1")}
    assert clusters[("squad", "s1")]["EWRA-Nearest"] == 0.75


def test_combined_meta_uses_equal_attempt_weight() -> None:
    first = {("old", "s1"): {
        "EWRA-Nearest": 0.6, "RandomResidualAudit": 0.5,
        "ShuffledSafeAudit": 0.5,
    }}
    second = {
        ("new", f"s{i}"): {
            "EWRA-Nearest": 0.9, "RandomResidualAudit": 0.5,
            "ShuffledSafeAudit": 0.5,
        }
        for i in range(100)
    }
    result = combined_meta(first, second, np.random.default_rng(20270920), 100)
    assert result["EWRA-Nearest_minus_RandomResidualAudit"][
        "equal_attempt_effect"
    ] == pytest.approx(0.25)

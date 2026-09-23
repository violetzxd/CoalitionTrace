#!/usr/bin/env python3
"""Frozen Confirmatory-II and equal-attempt meta-analysis.

The script consumes method-evaluation JSONL files.  Randomized seeds are first
averaged within a model-case, models are then averaged within a
``(dataset, source_id)`` cluster, and only those base-source clusters are
bootstrapped.  Confirmatory-I and II are resampled independently and receive
equal weight in the combined analysis.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import glob
import json
from pathlib import Path

import numpy as np


METHOD = "EWRA-Nearest"
BASELINES = ("RandomResidualAudit", "ShuffledSafeAudit")
METHODS = (METHOD,) + BASELINES
SEED = 20270920
DEFAULT_DRAWS = 20_000


def read_rows(patterns: list[str]) -> list[dict]:
    rows: list[dict] = []
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern))
    for filename in sorted(set(paths)):
        rows.extend(
            json.loads(line)
            for line in Path(filename).read_text(encoding="utf-8").splitlines()
            if line
        )
    return rows


def model_case_means(rows: list[dict]) -> dict[tuple[str, str, str, str], float]:
    grouped: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        if (row.get("stratum") == "N" and int(row.get("budget", -1)) == 48
                and row.get("method") in METHODS):
            key = (str(row["dataset"]), str(row["model"]),
                   str(row["source_id"]), str(row["method"]))
            grouped[key].append(float(row["detected_nonmonotone"]))
    return {key: float(np.mean(values)) for key, values in grouped.items()}


def base_clusters(rows: list[dict]) -> dict[tuple[str, str], dict[str, float]]:
    cases = model_case_means(rows)
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for (dataset, _model, source, method), value in cases.items():
        grouped[(dataset, source, method)].append(value)
    clusters: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for (dataset, source, method), values in grouped.items():
        clusters[(dataset, source)][method] = float(np.mean(values))
    return {key: values for key, values in clusters.items()
            if all(method in values for method in METHODS)}


def _quantiles(samples: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(samples, [0.025, 0.975])]


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator,
                   draws: int) -> tuple[float, list[float]]:
    if not len(values):
        return float("nan"), [float("nan"), float("nan")]
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), _quantiles(samples)


def summarize_clusters(clusters: dict[tuple[str, str], dict[str, float]],
                       rng: np.random.Generator, draws: int) -> dict:
    ordered = [clusters[key] for key in sorted(clusters)]
    result: dict[str, object] = {"clusters": len(ordered)}
    nearest = np.asarray([row[METHOD] for row in ordered], dtype=float)
    point, interval = bootstrap_mean(nearest, rng, draws)
    result[METHOD] = {"recall": point, "bootstrap95": interval,
                      "one_sided_97.5_lower": interval[0]}
    for baseline in BASELINES:
        values = np.asarray([row[METHOD] - row[baseline] for row in ordered], dtype=float)
        point, interval = bootstrap_mean(values, rng, draws)
        result[f"{METHOD}_minus_{baseline}"] = {
            "effect": point, "bootstrap95": interval,
            "one_sided_97.5_lower": interval[0],
        }
    return result


def cell_summaries(rows: list[dict], rng: np.random.Generator, draws: int) -> dict:
    cases = model_case_means(rows)
    cells = sorted({(dataset, model) for dataset, model, _source, _method in cases})
    output = {}
    for dataset, model in cells:
        sources = sorted({source for d, m, source, _method in cases
                          if d == dataset and m == model
                          and all((d, m, source, method) in cases for method in METHODS)})
        clusters = {
            (dataset, source): {
                method: cases[(dataset, model, source, method)] for method in METHODS
            }
            for source in sources
        }
        output[f"{dataset}:{model}"] = summarize_clusters(clusters, rng, draws)
    return output


def sample_floors(rows: list[dict]) -> dict:
    # One deterministic row per selected case avoids multiplying randomized seeds.
    selected = {
        (str(row["dataset"]), str(row["model"]), str(row["source_id"]),
         str(row["case_id"]), str(row["stratum"]))
        for row in rows
        if row.get("method") == "StandardEnumerator"
        and int(row.get("budget", -1)) == 48
    }
    cells = sorted({(dataset, model) for dataset, model, *_ in selected})
    counts = {}
    for dataset, model in cells:
        counts[f"{dataset}:{model}"] = {
            stratum: len({case_id for d, m, _source, case_id, s in selected
                          if d == dataset and m == model and s == stratum})
            for stratum in ("U", "A", "N")
        }
    n_by_dataset = {
        dataset: len({source for d, _m, source, _case, stratum in selected
                      if d == dataset and stratum == "N"})
        for dataset in sorted({d for d, *_ in selected})
    }
    n_total = len({(dataset, source) for dataset, _model, source, _case, stratum
                   in selected if stratum == "N"})
    passed = (
        len(cells) == 4
        and all(value["N"] >= 50 and value["U"] >= 30 and value["A"] >= 30
                for value in counts.values())
        and len(n_by_dataset) == 2
        and all(value >= 60 for value in n_by_dataset.values())
        and n_total >= 120
    )
    return {"cells": counts, "n_unique_sources_by_dataset": n_by_dataset,
            "n_unique_sources_total": n_total, "passed": passed}


def combined_meta(first: dict[tuple[str, str], dict[str, float]],
                  second: dict[tuple[str, str], dict[str, float]],
                  rng: np.random.Generator, draws: int) -> dict:
    result: dict[str, object] = {}
    first_rows = [first[key] for key in sorted(first)]
    second_rows = [second[key] for key in sorted(second)]
    for baseline in BASELINES:
        a = np.asarray([row[METHOD] - row[baseline] for row in first_rows])
        b = np.asarray([row[METHOD] - row[baseline] for row in second_rows])
        boot_a = rng.choice(a, size=(draws, len(a)), replace=True).mean(axis=1)
        boot_b = rng.choice(b, size=(draws, len(b)), replace=True).mean(axis=1)
        combined = (boot_a + boot_b) / 2.0
        result[f"{METHOD}_minus_{baseline}"] = {
            "attempt1_effect": float(a.mean()),
            "attempt2_effect": float(b.mean()),
            "equal_attempt_effect": float((a.mean() + b.mean()) / 2.0),
            "bootstrap95": _quantiles(combined),
            "one_sided_97.5_lower": float(np.quantile(combined, 0.025)),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt1", action="append", required=True)
    parser.add_argument("--attempt2", action="append", required=True)
    parser.add_argument("--invariants", type=Path, required=True,
                        help="JSON containing passed=true from the frozen invariant audit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    args = parser.parse_args()

    first_rows, second_rows = read_rows(args.attempt1), read_rows(args.attempt2)
    first, second = base_clusters(first_rows), base_clusters(second_rows)
    if not first or not second:
        raise ValueError("both attempts require complete paired N clusters")
    invariant_result = json.loads(args.invariants.read_text(encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    cells = cell_summaries(second_rows, rng, args.draws)
    pooled = summarize_clusters(second, rng, args.draws)
    floors = sample_floors(second_rows)
    meta = combined_meta(first, second, rng, args.draws)

    uniform = pooled[f"{METHOD}_minus_{BASELINES[0]}"]
    shuffled = pooled[f"{METHOD}_minus_{BASELINES[1]}"]
    recall = pooled[METHOD]
    positive_cells = sum(
        all(summary[f"{METHOD}_minus_{baseline}"]["effect"] > 0
            for baseline in BASELINES)
        for summary in cells.values()
    )
    no_bad_uniform_cell = all(
        summary[f"{METHOD}_minus_{BASELINES[0]}"]["effect"] >= -0.03
        for summary in cells.values()
    )
    meta_pass = all(
        value["attempt1_effect"] > 0
        and value["attempt2_effect"] > 0
        and value["one_sided_97.5_lower"] > 0
        for value in meta.values()
    )
    gates = {
        "uniform_effect_at_least_0.05": uniform["effect"] >= 0.05,
        "uniform_lower_above_zero": uniform["one_sided_97.5_lower"] > 0,
        "shuffled_lower_above_zero": shuffled["one_sided_97.5_lower"] > 0,
        "at_least_three_positive_cells": len(cells) == 4 and positive_cells >= 3,
        "no_uniform_cell_below_minus_0.03": no_bad_uniform_cell,
        "nearest_recall_at_least_0.88": recall["recall"] >= 0.88,
        "nearest_lower_at_least_0.83": recall["one_sided_97.5_lower"] >= 0.83,
        "sample_floors": floors["passed"],
        "combined_equal_attempt_meta": meta_pass,
        "identity_budget_soundness": bool(invariant_result.get("passed")),
    }
    output = {
        "confirmatory": True,
        "seed": SEED,
        "bootstrap_draws": args.draws,
        "one_sided_confidence": 0.975,
        "attempt1_clusters": len(first),
        "attempt2_clusters": len(second),
        "attempt2_cells": cells,
        "attempt2_pooled": pooled,
        "sample_floors": floors,
        "combined_equal_attempt_meta": meta,
        "invariant_audit": invariant_result,
        "gates": gates,
        "joint_success": all(gates.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"joint_success": output["joint_success"], "gates": gates}))


if __name__ == "__main__":
    main()

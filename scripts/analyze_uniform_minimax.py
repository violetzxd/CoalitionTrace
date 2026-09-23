#!/usr/bin/env python3
"""Check the static-witness hypergeometric model for prompt-uniform auditing."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from coalitiontrace.core import UtilityTable
from coalitiontrace.set_baselines import (
    random_residual_audited_enumerator, standard_monotone_enumerator,
)


def _violation(values: dict[int, float], tau: float = 1.0) -> bool:
    ones = [m for m, v in values.items() if v >= tau]
    zeros = [m for m, v in values.items() if v < tau]
    return any(lower != upper and lower & upper == lower
               for lower in ones for upper in zeros)


def _probability(total: int, witnesses: int, draws: int) -> float:
    draws = min(draws, total)
    if witnesses <= 0 or draws <= 0:
        return 0.0
    if draws > total - witnesses:
        return 1.0
    return 1.0 - math.comb(total - witnesses, draws) / math.comb(total, draws)


def _bootstrap(values: np.ndarray, rng: np.random.Generator, draws: int) -> list[float]:
    means = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def _base_dataset(dataset: str) -> str:
    if dataset.startswith("hotpot"):
        return "hotpotqa"
    if dataset.startswith("nq"):
        return "nq"
    return dataset.split("-", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", action="append", nargs=4, metavar=(
        "ORACLE", "SELECTION", "DATASET", "MODEL"), required=True)
    parser.add_argument("--budget", type=int, default=48)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--permutations", type=int, default=1000)
    args = parser.parse_args()

    case_rows: list[dict] = []
    for oracle_name, selection_name, dataset, model in args.spec:
        selected_rows = [json.loads(line) for line in Path(selection_name).read_text(
            encoding="utf-8").splitlines() if line]
        selected = {r["case_id"]: r for r in selected_rows if r["stratum"] == "N"}
        values: dict[str, dict[int, float]] = defaultdict(dict)
        keys: dict[str, dict[int, str | int]] = defaultdict(dict)
        for line in Path(oracle_name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            case_id = row["case_id"]
            if case_id in selected:
                mask = int(row["mask"])
                values[case_id][mask] = float(row["utility"])
                keys[case_id][mask] = row.get("prompt_sha256", mask)
        for case_id, truth in values.items():
            n = (len(truth)).bit_length() - 1
            table = UtilityTable(n, truth, query_keys=keys[case_id])
            standard_monotone_enumerator(table, args.budget)
            queried_keys = {table.query_key(mask) for mask in table.queries}
            class_members: dict[str | int, list[int]] = defaultdict(list)
            for mask in truth:
                class_members[table.query_key(mask)].append(mask)
            observed: dict[int, float] = {}
            for key in queried_keys:
                labels = {truth[m] for m in class_members[key]}
                if len(labels) != 1:
                    raise ValueError(f"inconsistent prompt class in {case_id}: {key}")
                observed.update({m: next(iter(labels)) for m in class_members[key]})
            prefix_violation = _violation(observed, table.tau)
            witness_classes = 0
            witness_hashes: set[str] = set()
            unqueried = [key for key in class_members if key not in queried_keys]
            for key in unqueried:
                labels = {truth[m] for m in class_members[key]}
                if len(labels) != 1:
                    raise ValueError(f"inconsistent prompt class in {case_id}: {key}")
                simulated = dict(observed)
                simulated.update({m: next(iter(labels)) for m in class_members[key]})
                is_witness = _violation(simulated, table.tau)
                witness_classes += int(is_witness)
                if is_witness:
                    witness_hashes.add(hashlib.sha256(str(key).encode()).hexdigest())
            residual = max(0, args.budget - table.unique_queries)
            predicted = (
                1.0 if prefix_violation
                else _probability(len(unqueried), witness_classes, residual)
            )
            sequential_hits = 0
            dynamic_only_hits = 0
            for seed in range(args.permutations):
                result = random_residual_audited_enumerator(
                    UtilityTable(n, truth, query_keys=keys[case_id]),
                    args.budget, seed=seed,
                )
                if result.observed_violation:
                    sequential_hits += 1
                    queried_initial_witness = any(
                        step["key_sha256"] in witness_hashes
                        for step in result.audit_trace
                    )
                    dynamic_only_hits += int(
                        result.witness_audit_query not in (None, 0)
                        and not queried_initial_witness
                    )
            case_rows.append({
                "dataset": dataset, "model": model, "case_id": case_id,
                "source_id": selected[case_id]["source_id"],
                "prefix_queries": table.unique_queries,
                "prefix_violation": prefix_violation,
                "unqueried_classes": len(unqueried),
                "static_witness_classes": witness_classes,
                "residual_budget": min(residual, len(unqueried)),
                "static_hypergeometric_detection": predicted,
                "sequential_detection_mc": sequential_hits / args.permutations,
                "dynamic_only_detection_mc": dynamic_only_hits / args.permutations,
            })

    clusters: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in case_rows:
        clusters[(_base_dataset(row["dataset"]), row["source_id"])].append(row)
    cluster_rows = []
    for (dataset, source), rows in clusters.items():
        predicted = float(np.mean([r["static_hypergeometric_detection"] for r in rows]))
        actuals = [r["sequential_detection_mc"] for r in rows]
        dynamic = [r["dynamic_only_detection_mc"] for r in rows]
        cluster_rows.append({
            "dataset": dataset, "source_id": source, "model_cases": len(rows),
            "predicted": predicted,
            "sequential_mc": float(np.mean(actuals)),
            "dynamic_only_mc": float(np.mean(dynamic)),
        })
    paired = cluster_rows
    predicted = np.array([r["predicted"] for r in paired])
    actual = np.array([r["sequential_mc"] for r in paired])
    dynamic = np.array([r["dynamic_only_mc"] for r in paired])
    difference = actual - predicted
    rng = np.random.default_rng(20270920)
    output = {
        "interpretation": (
            "Static-prefix formula; empirical excess can arise from witnesses "
            "created by multiple sequentially queried classes."
        ),
        "cases": len(case_rows), "source_clusters": len(paired),
        "mean_static_prediction": float(predicted.mean()),
        "permutations_per_case": args.permutations,
        "mean_sequential_detection_mc": float(actual.mean()),
        "mean_sequential_minus_static": float(difference.mean()),
        "difference_cluster_bootstrap95": _bootstrap(
            difference, rng, args.bootstrap),
        "mean_dynamic_only_detection_mc": float(dynamic.mean()),
        "dynamic_only_cluster_bootstrap95": _bootstrap(
            dynamic, rng, args.bootstrap),
        "case_rows": case_rows, "cluster_rows": cluster_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

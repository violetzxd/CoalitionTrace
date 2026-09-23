#!/usr/bin/env python3
"""Audit frozen Confirmatory-II identity, budget, and witness invariants."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from coalitiontrace.core import UtilityTable
from coalitiontrace.set_baselines import (
    exposure_weighted_audited_enumerator,
    random_residual_audited_enumerator,
    shuffled_safety_audited_enumerator,
    standard_monotone_enumerator,
)


BUDGET = 48
SEEDS = range(10)


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line]


def _sound(table: UtilityTable, witness: tuple[int, int] | None) -> bool:
    if witness is None:
        return True
    lower, upper = witness
    return (lower != upper and lower & upper == lower
            and table.values[lower] >= table.tau
            and table.values[upper] < table.tau)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    violations: list[dict] = []
    audited_cases = 0
    audited_runs = 0
    for cell in manifest["cells"]:
        grouped: dict[str, dict[int, float]] = defaultdict(dict)
        query_keys: dict[str, dict[int, str | int]] = defaultdict(dict)
        for row in _load_jsonl(Path(cell["oracle"])):
            case_id, mask = str(row["case_id"]), int(row["mask"])
            grouped[case_id][mask] = float(row["utility"])
            query_keys[case_id][mask] = row.get("prompt_sha256", mask)
        labels = {str(row["case_id"]): row for row in _load_jsonl(Path(cell["analysis"]))}
        selected = {str(row["case_id"]): row for row in _load_jsonl(Path(cell["selection"]))}
        for case_id in sorted(selected):
            audited_cases += 1
            if case_id not in grouped or case_id not in labels:
                violations.append({"case_id": case_id, "kind": "missing_oracle_or_label"})
                continue
            values, keys = grouped[case_id], query_keys[case_id]
            if len(values) != 256 or len(set(keys.values())) != 256:
                violations.append({"case_id": case_id, "kind": "incomplete_or_collapsed_oracle"})
                continue
            truth = tuple(labels[case_id]["minima"])
            standard_table = UtilityTable(8, values, query_keys=keys)
            standard = standard_monotone_enumerator(standard_table, BUDGET)
            standard_prefix = tuple(standard_table.query_key(mask)
                                    for mask in standard_table.queries)
            if standard_table.unique_queries > BUDGET or not _sound(
                    standard_table, standard.observed_violation):
                violations.append({"case_id": case_id, "kind": "standard_budget_or_soundness"})
            standard_acem = set(standard.causes) == set(truth)
            for seed in SEEDS:
                runners = {
                    "RandomResidualAudit": lambda table: random_residual_audited_enumerator(
                        table, BUDGET, seed=seed),
                    "ShuffledSafeAudit": lambda table: shuffled_safety_audited_enumerator(
                        table, BUDGET, seed=seed),
                    "EWRA-Nearest": lambda table: exposure_weighted_audited_enumerator(
                        table, BUDGET, seed=seed, variant="nearest"),
                }
                for method, runner in runners.items():
                    audited_runs += 1
                    table = UtilityTable(8, values, query_keys=keys)
                    result = runner(table)
                    prefix_length = result.enumeration_queries
                    prefix = tuple(table.query_key(mask)
                                   for mask in table.queries[:prefix_length])
                    if table.unique_queries > BUDGET:
                        violations.append({"case_id": case_id, "method": method,
                                           "seed": seed, "kind": "budget"})
                    if not _sound(table, result.observed_violation):
                        violations.append({"case_id": case_id, "method": method,
                                           "seed": seed, "kind": "unsound_witness"})
                    if labels[case_id]["stratum"] in {"U", "A"}:
                        identity = (
                            tuple(result.causes) == tuple(standard.causes)
                            and prefix == standard_prefix
                            and (set(result.causes) == set(truth)) == standard_acem
                        )
                        if not identity:
                            violations.append({"case_id": case_id, "method": method,
                                               "seed": seed, "kind": "ua_prefix_identity"})

    output = {
        "passed": not violations,
        "budget": BUDGET,
        "seeds": list(SEEDS),
        "audited_cases": audited_cases,
        "audited_method_runs": audited_runs,
        "violations": violations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": output["passed"], "audited_cases": audited_cases,
                      "audited_method_runs": audited_runs,
                      "violations": len(violations)}))


if __name__ == "__main__":
    main()

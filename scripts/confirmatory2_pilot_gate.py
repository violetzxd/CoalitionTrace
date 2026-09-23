#!/usr/bin/env python3
"""Feasibility-only Confirmatory-II pilot gate.

This intentionally emits no case-level labels, transition tables, minima, or
method results.  It reveals only the quantities allowed by the frozen pilot.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from coalitiontrace.core import CoalitionCase


def _read_cases(path: Path) -> dict[str, CoalitionCase]:
    return {
        case.case_id: case
        for case in (
            CoalitionCase.from_json(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines() if line
        )
    }


def _is_n(values: dict[int, float], n: int) -> bool:
    full = (1 << n) - 1
    if values[0] >= 1.0 or values[full] < 1.0:
        return False
    for lower in range(1 << n):
        if values[lower] < 1.0:
            continue
        remaining = full & ~lower
        while remaining:
            bit = remaining & -remaining
            if values[lower | bit] < 1.0:
                return True
            remaining -= bit
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", action="append", nargs=4, required=True,
                        metavar=("LABEL", "DATASET", "CASES", "ORACLE"))
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    collisions = int(preflight.get("generic_request_collisions", 0)) + sum(
        int(value) for value in preflight.get("chat_template_collisions", {}).values()
    )
    cell_counts: dict[str, int] = {}
    dataset_sources: dict[str, set[str]] = defaultdict(set)
    invalid_tables = 0
    for label, dataset, cases_name, oracle_name in args.cell:
        cases = _read_cases(Path(cases_name))
        grouped: dict[str, dict[int, float]] = defaultdict(dict)
        duplicate_rows = 0
        for line in Path(oracle_name).read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            row = json.loads(line)
            case_id, mask = str(row["case_id"]), int(row["mask"])
            if mask in grouped[case_id]:
                duplicate_rows += 1
            grouped[case_id][mask] = float(row["utility"])
        invalid_tables += duplicate_rows
        realized_sources = set()
        for case_id, case in cases.items():
            values = grouped.get(case_id, {})
            expected = 1 << case.n
            if len(values) != expected or set(values) != set(range(expected)):
                invalid_tables += 1
                continue
            if _is_n(values, case.n):
                realized_sources.add(case.source_id)
        unexpected = set(grouped) - set(cases)
        invalid_tables += len(unexpected)
        cell_counts[label] = len(realized_sources)
        dataset_sources[dataset].update(realized_sources)

    unique_by_dataset = {key: len(value) for key, value in sorted(dataset_sources.items())}
    passed = (
        len(cell_counts) == 4
        and all(value >= 20 for value in cell_counts.values())
        and len(unique_by_dataset) == 2
        and all(value >= 20 for value in unique_by_dataset.values())
        and collisions == 0
        and invalid_tables == 0
    )
    output = {
        "pilot_scope": "feasibility_only_no_method_statistics",
        "realized_n_sources_by_cell": cell_counts,
        "unique_realized_n_sources_by_dataset": unique_by_dataset,
        "request_collisions": collisions,
        "invalid_oracle_tables": invalid_tables,
        "decision": "GO" if passed else "STOP",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()

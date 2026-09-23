#!/usr/bin/env python3
"""Summarize exact zero-hit witness-resolution for a minimax artifact."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from coalitiontrace.audit_bounds import zero_hit_upper_bound


def _summary(rows: list[dict], alpha: float) -> dict:
    resolved = []
    unresolved_cases = 0
    upper_counts = []
    fractions = []
    for row in rows:
        population = int(row["unqueried_classes"])
        draws = min(int(row["residual_budget"]), population)
        upper = zero_hit_upper_bound(population, draws, alpha)
        upper_counts.append(upper)
        fractions.append(upper / population if population else 0.0)
        if population and upper < population:
            resolved.append((upper + 1) / population)
        else:
            unresolved_cases += 1
    resolved_array = np.asarray(resolved, dtype=float)
    return {
        "cases": len(rows),
        "median_upper_count": float(np.median(upper_counts)),
        "median_upper_fraction": float(np.median(fractions)),
        "upper_fraction_q25_q75": [
            float(x) for x in np.quantile(fractions, [0.25, 0.75])
        ],
        "cases_with_no_nonvacuous_density_resolution": unresolved_cases,
        "median_min_excludable_density": (
            float(np.median(resolved_array)) if len(resolved_array) else None
        ),
        "min_excludable_density_q25_q75": [
            float(x) for x in np.quantile(resolved_array, [0.25, 0.75])
        ] if len(resolved_array) else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    artifact = json.loads(args.input.read_text(encoding="utf-8"))
    all_rows = artifact["case_rows"]
    rows = [row for row in all_rows if not row.get("prefix_violation", False)]
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[str(row["dataset"])].append(row)
    output = {
        "status": "post_hoc_descriptive",
        "alpha": args.alpha,
        "estimand": "fixed-prefix initial one-step witness classes",
        "warning": (
            "A zero-hit bound is a randomized-design resolution statement, "
            "not a monotonicity or cause-completeness certificate."
        ),
        "all_n_cases": len(all_rows),
        "eligible_no_prefix_violation_cases": len(rows),
        "prefix_detected_cases_excluded": len(all_rows) - len(rows),
        "pooled": _summary(rows, args.alpha),
        "by_dataset": {
            key: _summary(value, args.alpha) for key, value in sorted(groups.items())
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

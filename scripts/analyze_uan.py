from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from coalitiontrace.core import UtilityTable


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2


def edge_violations(table: UtilityTable) -> list[tuple[int, int]]:
    violations = []
    full = (1 << table.n) - 1
    for lower in range(1 << table.n):
        if not table.sufficient(lower):
            continue
        remaining = full & ~lower
        while remaining:
            bit = remaining & -remaining
            upper = lower | bit
            if not table.sufficient(upper):
                violations.append((lower, upper))
            remaining -= bit
    return violations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    grouped: dict[str, dict[int, float]] = defaultdict(dict)
    meta = {}
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line)
        grouped[row["case_id"]][int(row["mask"])] = float(row["utility"])
        meta[row["case_id"]] = row
    output = []
    for case_id, values in sorted(grouped.items()):
        n = int(meta[case_id]["n"])
        table = UtilityTable(n, values)
        if not table.complete():
            continue
        minima = table.inclusion_minima()
        violations = edge_violations(table)
        empty_ok, full_ok = not table.sufficient(0), table.sufficient((1 << n) - 1)
        if not (empty_ok and full_ok):
            stratum = "OOS"
        elif violations:
            stratum = "N"
        elif len(minima) == 1:
            stratum = "U"
        elif len(minima) >= 2:
            stratum = "A"
        else:
            stratum = "OOS"
        backbone = (1 << n) - 1
        for cause in minima:
            backbone &= cause
        overlaps = []
        for i, first in enumerate(minima):
            for second in minima[i + 1:]:
                overlaps.append((first & second).bit_count() / (first | second).bit_count())
        layers = [lower.bit_count() for lower, _ in violations]
        output.append({
            "case_id": case_id, "family": meta[case_id]["family"],
            "stratum": stratum, "empty_zero": empty_ok, "full_one": full_ok,
            "minima": list(minima), "cause_count": len(minima),
            "cause_sizes": [mask.bit_count() for mask in minima],
            "backbone": backbone, "backbone_size": backbone.bit_count(),
            "mean_pairwise_jaccard": sum(overlaps) / len(overlaps) if overlaps else None,
            "violation_edges": len(violations),
            "violation_rate": len(violations) / (n * (1 << (n - 1))),
            "violation_min_layer": min(layers) if layers else None,
            "violation_median_layer": _median(layers) if layers else None,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row) + "\n")
    print(json.dumps({
        "complete_cases": len(output),
        "strata": dict(Counter(row["stratum"] for row in output)),
        "by_family": {
            family: dict(Counter(row["stratum"] for row in output if row["family"] == family))
            for family in sorted({row["family"] for row in output})
        },
    }, indent=2))


if __name__ == "__main__":
    main()

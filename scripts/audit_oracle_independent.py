from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random


def independent_minima(values: dict[int, float], n: int) -> list[int]:
    sufficient = [mask for mask, value in values.items() if value >= 1.0]
    return sorted(
        mask for mask in sufficient
        if not any(sub != mask and (sub & mask) == sub for sub in sufficient)
    )


def independent_monotone(values: dict[int, float], n: int) -> bool:
    for lower in range(1 << n):
        for upper in range(1 << n):
            if (lower & upper) == lower and values[lower] > values[upper]:
                return False
    return True


def independent_stratum(values: dict[int, float], n: int, minima: list[int]) -> str:
    full = (1 << n) - 1
    if values[0] >= 1.0 or values[full] < 1.0:
        return "OOS"
    if not independent_monotone(values, n):
        return "N"
    if len(minima) == 1:
        return "U"
    if len(minima) >= 2:
        return "A"
    return "OOS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--fraction", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=20270920)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    values = defaultdict(dict)
    ns = {}
    for row in map(json.loads, args.oracle.open(encoding="utf-8")):
        values[row["case_id"]][int(row["mask"])] = float(row["utility"])
        ns[row["case_id"]] = int(row["n"])
    labels = {row["case_id"]: row for row in
              map(json.loads, args.analysis.open(encoding="utf-8"))}
    ids = sorted(set(values) & set(labels))
    random.Random(args.seed).shuffle(ids)
    ids = ids[:max(1, round(args.fraction * len(ids)))]
    mismatches = []
    for case_id in ids:
        minima = independent_minima(values[case_id], ns[case_id])
        stratum = independent_stratum(values[case_id], ns[case_id], minima)
        expected_minima = sorted(labels[case_id]["minima"])
        if minima != expected_minima or stratum != labels[case_id]["stratum"]:
            mismatches.append({
                "case_id": case_id,
                "expected_minima": expected_minima,
                "independent_minima": minima,
                "expected_stratum": labels[case_id]["stratum"],
                "independent_stratum": stratum,
            })
    payload = {
        "seed": args.seed,
        "fraction": args.fraction,
        "audited_cases": len(ids),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

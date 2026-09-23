from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from coalitiontrace.core import CoalitionCase


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def band(label: dict) -> str:
    sizes = label["cause_sizes"]
    overlap = label.get("mean_pairwise_jaccard") or 0.0
    return (
        f"k{label['cause_count']}-s{max(sizes, default=0)}-"
        f"{'overlap' if overlap > 0 else 'disjoint'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=48)
    args = parser.parse_args()

    cases = {
        case.case_id: case
        for case in (
            CoalitionCase.from_json(json.loads(line))
            for line in args.cases.open(encoding="utf-8")
        )
    }
    labels = {
        row["case_id"]: row
        for row in map(json.loads, args.analysis.open(encoding="utf-8"))
    }
    selected = {
        row["case_id"]: row
        for row in map(json.loads, args.selection.open(encoding="utf-8"))
    }
    evaluations = [
        row for row in map(json.loads, args.evaluation.open(encoding="utf-8"))
        if row["budget"] == args.budget and row["case_id"] in selected
    ]

    case_rows = []
    for case_id, selection in selected.items():
        case, label = cases[case_id], labels[case_id]
        realized = set(label["minima"])
        planted = {
            sum(1 << i for i in cause) for cause in case.planted_causes
        }
        case_rows.append({
            "case_id": case_id,
            "source_id": selection["source_id"],
            "stratum": selection["stratum"],
            "family": label["family"],
            "difficulty_band": band(label),
            "cause_count": label["cause_count"],
            "cause_sizes": label["cause_sizes"],
            "backbone_size": label["backbone_size"],
            "mean_pairwise_jaccard": label.get("mean_pairwise_jaccard"),
            "planted_exact": realized == planted,
            "cross_path_causes": len(realized - planted),
        })

    features = {row["case_id"]: row for row in case_rows}
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in evaluations:
        groups[(row["stratum"], row["method"], features[row["case_id"]]["difficulty_band"])].append(row)
    performance = []
    for (stratum, method, difficulty), rows in sorted(groups.items()):
        performance.append({
            "stratum": stratum,
            "method": method,
            "difficulty_band": difficulty,
            "source_queries": len({row["source_id"] for row in rows}),
            "runs": len(rows),
            "acem": mean(row["acem"] for row in rows),
            "cause_f1": mean(row["cause_f1"] for row in rows),
            "prompt_queries": mean(row["queries"] for row in rows),
            "mask_queries": mean(row["mask_queries"] for row in rows),
        })

    payload = {
        "budget": args.budget,
        "selected_counts": dict(Counter(row["stratum"] for row in case_rows)),
        "family_counts": dict(Counter(row["family"] for row in case_rows)),
        "difficulty_counts": dict(Counter(row["difficulty_band"] for row in case_rows)),
        "cause_size_counts": dict(Counter(
            size for row in case_rows if row["stratum"] == "A" for size in row["cause_sizes"]
        )),
        "A_cross_path_cases": sum(
            row["cross_path_causes"] > 0 for row in case_rows if row["stratum"] == "A"
        ),
        "A_planted_exact_rate": mean(
            row["planted_exact"] for row in case_rows if row["stratum"] == "A"
        ),
        "performance": performance,
        "cases": case_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items()
                      if key not in {"performance", "cases"}}, indent=2))


if __name__ == "__main__":
    main()

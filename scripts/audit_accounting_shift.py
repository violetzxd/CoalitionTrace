from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


METHODS = ("AmbiCause", "RepeatedGreedy", "RandomMasks")


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def load(path: Path, budget: int) -> list[dict]:
    return [
        row for row in map(json.loads, path.open(encoding="utf-8"))
        if row["stratum"] == "A" and row["budget"] == budget
    ]


def aggregate(rows: list[dict]) -> dict[str, dict]:
    output = {}
    for method in METHODS:
        by_source = defaultdict(list)
        for row in rows:
            if row["method"] == method:
                by_source[row["source_id"]].append(row)
        source_rows = []
        for source_id, members in by_source.items():
            source_rows.append({
                "source_id": source_id,
                "acem": mean(float(row["acem"]) for row in members),
                "queries": mean(float(row["queries"]) for row in members),
                "input_tokens": mean(float(row.get("input_tokens", 0)) for row in members),
                "output_tokens": mean(float(row.get("output_tokens", 0)) for row in members),
            })
        output[method] = {
            "sources": len(source_rows),
            "acem": mean(row["acem"] for row in source_rows),
            "queries": mean(row["queries"] for row in source_rows),
            "input_tokens": mean(row["input_tokens"] for row in source_rows),
            "output_tokens": mean(row["output_tokens"] for row in source_rows),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, nargs="+", required=True)
    parser.add_argument("--fair", type=Path, nargs="+", required=True)
    parser.add_argument("--labels", nargs="+", required=True)
    parser.add_argument("--budget", type=int, default=48)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (len(args.old) == len(args.fair) == len(args.labels)):
        raise ValueError("old, fair and labels must have equal lengths")
    cells = []
    for label, old_path, fair_path in zip(args.labels, args.old, args.fair):
        old_rows, fair_rows = load(old_path, args.budget), load(fair_path, args.budget)
        fair_agg = aggregate(fair_rows)
        representatives = {}
        for row in fair_rows:
            representatives.setdefault(row["source_id"], row)
        collapse = [
            row["oracle_unique_prompts"] / row["oracle_total_masks"]
            for row in representatives.values()
        ]
        cells.append({
            "cell": label,
            "budget": args.budget,
            "old_budget_unit": "syntactic masks",
            "fair_budget_unit": "unique complete-prompt hashes",
            "old": aggregate(old_rows),
            "fair": fair_agg,
            "oracle_prompt_fraction_mean": mean(collapse),
            "oracle_prompt_fraction_min": min(collapse),
            "oracle_prompt_fraction_max": max(collapse),
            "adapt_minus_repeated_old": (
                aggregate(old_rows)["AmbiCause"]["acem"]
                - aggregate(old_rows)["RepeatedGreedy"]["acem"]
            ),
            "adapt_minus_repeated_fair": (
                fair_agg["AmbiCause"]["acem"] - fair_agg["RepeatedGreedy"]["acem"]
            ),
        })
    payload = {"cells": cells}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

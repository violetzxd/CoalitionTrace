from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


def mean(rows, key):
    return sum(float(row[key]) for row in rows) / len(rows) if rows else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for path in args.input for line in path.open(encoding="utf-8")]
    groups = defaultdict(list)
    for row in rows:
        groups[(row["dataset"], row["model"], row["stratum"],
                row["budget"], row["method"])].append(row)
    summary = []
    for (dataset, model, stratum, budget, method), group in sorted(groups.items()):
        summary.append({
            "dataset": dataset, "model": model, "stratum": stratum,
            "budget": budget, "method": method,
            "source_queries": len({row["source_id"] for row in group}),
            "runs": len(group), "acem": mean(group, "acem"),
            "any_cause": mean(group, "any_cause"),
            "cause_precision": mean(group, "cause_precision"),
            "cause_recall": mean(group, "cause_recall"),
            "cause_f1": mean(group, "cause_f1"),
            "false_cause": mean(group, "false_cause"),
            "queries": mean(group, "queries"),
            "input_tokens": mean(group, "input_tokens") if "input_tokens" in group[0] else None,
            "output_tokens": mean(group, "output_tokens") if "output_tokens" in group[0] else None,
            "mask_queries": mean(group, "mask_queries") if "mask_queries" in group[0] else None,
            "oracle_unique_prompts": mean(group, "oracle_unique_prompts")
            if "oracle_unique_prompts" in group[0] else None,
            "oracle_total_masks": mean(group, "oracle_total_masks")
            if "oracle_total_masks" in group[0] else None,
            "n_detection": mean(group, "detected_nonmonotone"),
            "unsafe_unconditional_complete": mean(group, "unconditional_complete"),
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

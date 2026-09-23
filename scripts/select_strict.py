from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-family", type=int, default=20)
    args = parser.parse_args()
    grouped = defaultdict(dict)
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line)
        grouped[row["case_id"]][int(row["mask"])] = int(row["utility"])
    poison_masks = {}
    for line in args.cases.open(encoding="utf-8"):
        row = json.loads(line)
        poison = sum(1 << int(i) for i in row["poison_indices"])
        poison_masks[row["case_id"]] = (len(row["observed"]), poison)
    counts = defaultdict(int); selected = []
    for case_id, values in sorted(grouped.items()):
        family = case_id.split(":", 1)[0]
        n, poison = poison_masks[case_id]
        full = (1 << n) - 1
        base = full & ~poison
        singleton_masks = [base | (1 << i) for i in range(n) if poison & (1 << i)]
        strict = values.get(full) == 1 and values.get(base, 0) == 0 and all(
            values.get(mask, 0) == 0 for mask in singleton_masks
        )
        if strict and counts[family] < args.per_family:
            selected.append(case_id); counts[family] += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(selected) + ("\n" if selected else ""), encoding="utf-8")
    print(json.dumps({"selected": len(selected), "by_family": counts}))


if __name__ == "__main__":
    main()

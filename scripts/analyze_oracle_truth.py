from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from coalitiontrace.core import UtilityTable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output-ids", type=Path)
    args = parser.parse_args()
    grouped = defaultdict(dict); family = {}
    poison_masks = {}
    for line in args.cases.open(encoding="utf-8"):
        row = json.loads(line)
        poison_masks[row["case_id"]] = sum(1 << int(i) for i in row["poison_indices"])
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line); cid = row["case_id"]
        grouped[cid][int(row["mask"])] = float(row["utility"])
        family[cid] = row["family"]
    rows = []
    for cid, values in grouped.items():
        n = max(values).bit_length()
        table = UtilityTable(n, values)
        minima = table.oracle_minima() if table.complete() else ()
        rows.append({
            "case_id": cid, "family": family[cid], "complete": table.complete(),
            "minimum_size": min((m.bit_count() for m in minima), default=None),
            "minimum_count": len(minima),
            "poison_pair_is_minimum": poison_masks.get(cid) in minima,
            "minima": minima,
        })
    summary = Counter()
    for row in rows:
        summary[(row["family"], row["complete"], row["minimum_size"], row["poison_pair_is_minimum"])] += 1
    for key, count in sorted(summary.items(), key=str):
        print(key, count)
    accepted = [row["case_id"] for row in rows if row["complete"] and row["poison_pair_is_minimum"]]
    print(json.dumps({"complete_cases": sum(r["complete"] for r in rows), "global_pair_cases": len(accepted)}))
    if args.output_ids:
        args.output_ids.parent.mkdir(parents=True, exist_ok=True)
        args.output_ids.write_text("\n".join(accepted) + ("\n" if accepted else ""), encoding="utf-8")


if __name__ == "__main__":
    main()

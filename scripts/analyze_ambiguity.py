from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from coalitiontrace.core import UtilityTable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    grouped = defaultdict(dict); meta = {}
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line); cid = row["case_id"]
        grouped[cid][int(row["mask"])] = float(row["utility"]); meta[cid] = row
    rows = []
    for cid, values in sorted(grouped.items()):
        n = int(meta[cid]["n"]); table = UtilityTable(n, values)
        if not table.complete():
            continue
        minima = table.inclusion_minima(); monotone = table.is_monotone()
        stratum = "U" if monotone and len(minima) == 1 else ("A" if monotone else "N")
        backbone = table.loo_backbone()
        intersection = (1 << n) - 1
        for cause in minima:
            intersection &= cause
        rows.append({"case_id": cid, "family": meta[cid]["family"], "stratum": stratum,
                     "monotone": monotone, "inclusion_minima": list(minima),
                     "ambiguity": len(minima), "loo_backbone": backbone,
                     "cause_intersection": intersection,
                     "theorem_holds": (not monotone) or backbone == intersection})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row) for row in rows) + ("\n" if rows else ""), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "strata": Counter(r["stratum"] for r in rows),
                      "theorem_violations": sum(not r["theorem_holds"] for r in rows)}, default=dict))


if __name__ == "__main__":
    main()

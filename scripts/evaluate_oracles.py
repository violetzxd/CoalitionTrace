from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from coalitiontrace.baselines import ddmin, greedy_deletion, kernel_shap, loo_rank, random_search
from coalitiontrace.core import UtilityTable
from coalitiontrace.metrics import exact_any, member_f1_any
from coalitiontrace.search import coalition_trace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=32)
    parser.add_argument("--case-ids", type=Path)
    args = parser.parse_args()
    selected = None
    if args.case_ids:
        selected = {line.strip() for line in args.case_ids.open(encoding="utf-8") if line.strip()}
    grouped = defaultdict(dict); metadata = {}
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line); cid = row["case_id"]
        if selected is not None and cid not in selected:
            continue
        grouped[cid][int(row["mask"])] = float(row["utility"])
        metadata[cid] = row
    method_names = ("CoalitionTrace", "Linear", "Random", "Greedy", "HierarchicalDeletion", "LOO", "KernelSHAP")
    rows = []
    for cid, values in sorted(grouped.items()):
        n = int(metadata[cid]["n"]); base = UtilityTable(n, values)
        if not base.complete():
            continue
        minima = base.oracle_minima()
        case_seed = int(hashlib.sha256(f"{cid}:evaluation-v1".encode()).hexdigest()[:8], 16)
        methods = {
            "CoalitionTrace": lambda t: coalition_trace(t, args.budget, max_size=2, seed=case_seed),
            "Linear": lambda t: coalition_trace(t, args.budget, max_size=2, pairwise=False, seed=case_seed),
            "Random": lambda t: random_search(t, args.budget, max_size=2, seed=case_seed),
            "Greedy": lambda t: greedy_deletion(t, args.budget),
            "HierarchicalDeletion": lambda t: ddmin(t, args.budget),
            "LOO": lambda t: loo_rank(t, args.budget),
            "KernelSHAP": lambda t: kernel_shap(t, args.budget, seed=case_seed),
        }
        for name, method in methods.items():
            result = method(base.fork())
            row = {
                "case_id": cid, "family": metadata[cid]["family"], "method": name,
                "mask": result.mask, "oracle_minima": list(minima),
                "ecm": exact_any(result.mask, minima), "member_f1": member_f1_any(result.mask, minima),
                "valid": int(result.verified_1_minimal), "queries": result.queries,
            }
            rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""), encoding="utf-8")
    for name in method_names:
        subset = [r for r in rows if r["method"] == name]
        if subset:
            print(name, {k: round(float(np.mean([r[k] for r in subset])), 4) for k in ("ecm", "member_f1", "valid", "queries")})


if __name__ == "__main__":
    main()

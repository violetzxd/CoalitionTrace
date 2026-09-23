from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest


def paired_bootstrap(a, b, repeats=10000, seed=20270920):
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    deltas = np.empty(repeats)
    for i in range(repeats):
        idx = rng.integers(0, len(a), len(a))
        deltas[i] = np.mean(a[idx] - b[idx])
    return float(np.mean(a-b)), tuple(float(x) for x in np.quantile(deltas, [.025, .975]))


def mcnemar_exact(a, b):
    n10 = sum(x == 1 and y == 0 for x, y in zip(a, b))
    n01 = sum(x == 0 and y == 1 for x, y in zip(a, b))
    p = 1.0 if n10+n01 == 0 else binomtest(min(n10, n01), n10+n01, .5).pvalue
    odds = float("inf") if n01 == 0 and n10 else ((n10 + .5) / (n01 + .5))
    return n10, n01, float(p), odds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--reference", default="CoalitionTrace")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.results.open(encoding="utf-8")]
    by_method = defaultdict(dict)
    for row in rows:
        by_method[row["method"]][row["case_id"]] = row
    ref = by_method[args.reference]
    output = {}
    for method, values in sorted(by_method.items()):
        if method == args.reference:
            continue
        ids = sorted(set(ref) & set(values))
        ra = [ref[i]["ecm"] for i in ids]; rb = [values[i]["ecm"] for i in ids]
        delta, ci = paired_bootstrap(ra, rb)
        n10, n01, p, odds = mcnemar_exact(ra, rb)
        output[method] = {"n": len(ids), "ecm_delta": delta, "ci95": ci,
                          "mcnemar_n10": n10, "mcnemar_n01": n01,
                          "mcnemar_p": p, "matched_odds_ratio": odds}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

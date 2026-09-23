from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest


def read_rows(paths: list[Path], method: str) -> dict[tuple[str, str, str], int]:
    rows = {}
    for path in paths:
        for line in path.open(encoding="utf-8"):
            row = json.loads(line)
            if (row["method"] == method and row["budget"] == 48
                    and row["stratum"] == "N"):
                rows[(row["dataset"], row["model"], row["case_id"])] = int(
                    row["detected_nonmonotone"]
                )
    return rows


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [center - half, center + half]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--safe", type=Path, nargs="+", required=True)
    parser.add_argument("--baseline", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20270920)
    args = parser.parse_args()
    safe = read_rows(args.safe, "SafeEnumerator")
    baseline = read_rows(args.baseline, "AmbiCause")
    if set(safe) != set(baseline):
        raise ValueError("Safe and baseline source keys differ")
    grouped = defaultdict(list)
    for key in sorted(safe):
        grouped[key[:2]].append((baseline[key], safe[key]))
    rng = np.random.default_rng(args.seed)
    cells = []
    for (dataset, model), pairs in grouped.items():
        array = np.asarray(pairs, dtype=float)
        n = len(array)
        base_k, safe_k = int(array[:, 0].sum()), int(array[:, 1].sum())
        gains = array[:, 1] - array[:, 0]
        samples = rng.integers(0, n, size=(args.bootstrap, n))
        boot = gains[samples].mean(axis=1)
        n01 = int(((array[:, 0] == 0) & (array[:, 1] == 1)).sum())
        n10 = int(((array[:, 0] == 1) & (array[:, 1] == 0)).sum())
        discordant = n01 + n10
        p = 1.0 if not discordant else float(
            binomtest(min(n01, n10), discordant, .5).pvalue
        )
        cells.append({
            "dataset": dataset, "model": model, "n": n,
            "baseline_recall": base_k / n, "safe_recall": safe_k / n,
            "safe_wilson95": wilson(safe_k, n),
            "paired_gain": float(gains.mean()),
            "paired_gain_bootstrap95": [float(x) for x in np.quantile(boot, [.025, .975])],
            "mcnemar_n01": n01, "mcnemar_n10": n10, "mcnemar_p": p,
        })
    pooled_pairs = np.asarray([pair for pairs in grouped.values() for pair in pairs])
    pooled_k = int(pooled_pairs[:, 1].sum())
    result = {"cells": cells, "pooled": {
        "n": len(pooled_pairs), "detected": pooled_k,
        "recall": pooled_k / len(pooled_pairs),
        "wilson95": wilson(pooled_k, len(pooled_pairs)),
    }}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

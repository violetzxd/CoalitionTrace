from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import binomtest


def percentile_ci(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def holm_adjust(pvalues: list[float]) -> list[float]:
    """Return Holm step-down adjusted p-values in the original order."""
    if not pvalues:
        return []
    order = np.argsort(np.asarray(pvalues))
    adjusted = np.empty(len(pvalues), dtype=float)
    running = 0.0
    m = len(pvalues)
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * pvalues[int(index)])
        adjusted[int(index)] = min(1.0, running)
    return adjusted.tolist()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method", default="AmbiCause")
    parser.add_argument("--baseline", default="RepeatedGreedy")
    parser.add_argument("--budget", type=int, default=48)
    parser.add_argument(
        "--baseline-seed", default="mean",
        help="Integer seed or 'mean' to average stochastic runs within source.",
    )
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20270920)
    parser.add_argument(
        "--holm-stratum",
        default="A",
        help="Apply Holm correction jointly to this stratum across input cells; use 'all' for every row.",
    )
    args = parser.parse_args()
    rows = [json.loads(line) for path in args.input for line in path.open(encoding="utf-8")]
    output = []
    cells = sorted({(row.get("dataset", "unknown"), row.get("model", "unknown"), row["stratum"])
                    for row in rows if row["budget"] == args.budget})
    rng = np.random.default_rng(args.seed)
    for dataset, model, stratum in cells:
        selected = [row for row in rows if row["budget"] == args.budget
                    and row.get("dataset", "unknown") == dataset
                    and row.get("model", "unknown") == model and row["stratum"] == stratum]
        method = {r["source_id"]: r for r in selected if r["method"] == args.method}
        baseline_rows = [r for r in selected if r["method"] == args.baseline]
        if args.baseline_seed == "mean":
            by_source = defaultdict(list)
            for row in baseline_rows:
                by_source[row["source_id"]].append(row)
            baseline = {
                source_id: {
                    "acem": float(np.mean([row["acem"] for row in source_rows])),
                    "cause_f1": float(np.mean([row["cause_f1"] for row in source_rows])),
                    "queries": float(np.mean([row["queries"] for row in source_rows])),
                }
                for source_id, source_rows in by_source.items()
            }
        else:
            baseline_seed = int(args.baseline_seed)
            baseline = {r["source_id"]: r for r in baseline_rows
                        if r["seed"] == baseline_seed}
        ids = sorted(method.keys() & baseline.keys())
        if not ids:
            continue
        diffs = np.asarray([method[i]["acem"] - baseline[i]["acem"] for i in ids])
        f1diffs = np.asarray([method[i]["cause_f1"] - baseline[i]["cause_f1"] for i in ids])
        calldiffs = np.asarray([method[i]["queries"] - baseline[i]["queries"] for i in ids])
        draws = rng.integers(0, len(ids), size=(args.bootstrap, len(ids)))
        m_only = sum(method[i]["acem"] > baseline[i]["acem"] for i in ids)
        b_only = sum(method[i]["acem"] < baseline[i]["acem"] for i in ids)
        discordant = m_only + b_only
        binary_baseline = all(baseline[i]["acem"] in {0.0, 1.0} for i in ids)
        mcnemar_p = (
            float(binomtest(min(m_only, b_only), discordant, .5).pvalue)
            if discordant and binary_baseline else (1.0 if binary_baseline else None)
        )
        output.append({
            "dataset": dataset, "model": model, "stratum": stratum, "n": len(ids),
            "method_acem": float(np.mean([method[i]["acem"] for i in ids])),
            "baseline_acem": float(np.mean([baseline[i]["acem"] for i in ids])),
            "acem_difference": float(diffs.mean()),
            "acem_difference_ci95": percentile_ci(diffs[draws].mean(axis=1)),
            "cause_f1_difference": float(f1diffs.mean()),
            "cause_f1_difference_ci95": percentile_ci(f1diffs[draws].mean(axis=1)),
            "call_difference": float(calldiffs.mean()),
            "call_difference_ci95": percentile_ci(calldiffs[draws].mean(axis=1)),
            "mcnemar_method_only": m_only, "mcnemar_baseline_only": b_only,
            "mcnemar_exact_p": mcnemar_p,
            "method_better_fraction": m_only / len(ids),
            "baseline_better_fraction": b_only / len(ids),
            "baseline_seed_rule": args.baseline_seed,
        })
    family = list(range(len(output))) if args.holm_stratum == "all" else [
        i for i, row in enumerate(output) if row["stratum"] == args.holm_stratum
    ]
    holm_family = [i for i in family if output[i]["mcnemar_exact_p"] is not None]
    adjusted = holm_adjust([output[i]["mcnemar_exact_p"] for i in holm_family])
    for i, p_adjusted in zip(holm_family, adjusted):
        output[i]["mcnemar_holm_family"] = args.holm_stratum
        output[i]["mcnemar_holm_family_size"] = len(holm_family)
        output[i]["mcnemar_holm_p"] = p_adjusted
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

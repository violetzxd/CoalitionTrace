#!/usr/bin/env python3
"""Source-clustered summaries for residual-budget safety audits."""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def regime(dataset: str) -> str:
    if "active" in dataset:
        return "active"
    if "news" in dataset:
        return "news"
    return "registry"


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator, draws: int) -> list[float]:
    sampled = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return [float(x) for x in np.quantile(sampled, [0.025, 0.975])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uniform", required=True)
    parser.add_argument("--ablation", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=10000)
    args = parser.parse_args()
    rng = np.random.default_rng(202709)

    rows = [row for path in glob.glob(args.uniform) for row in read_jsonl(path)]
    ablations = [row for path in glob.glob(args.ablation) for row in read_jsonl(path)]
    all_rows = rows + ablations
    grouped: dict[tuple[str, str, str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in all_rows:
        if row["stratum"] != "N":
            continue
        # The same source query evaluated under two generators is one sampling
        # cluster; retain all model/seed rows within (dataset, source_id).
        key = (regime(row["dataset"]), row["dataset"], row["method"], row["source_id"])
        grouped[key]["detected"].append(float(row["detected_nonmonotone"]))
        grouped[key]["queries"].append(float(row["queries"]))
        if row.get("audit_queries") is not None:
            grouped[key]["audit_queries"].append(float(row["audit_queries"]))
        if row.get("witness_audit_query") is not None:
            grouped[key]["witness"].append(float(row["witness_audit_query"]))

    # Deduplicate the Uniform method: its final prompt-uniform files supersede the
    # earlier mask-uniform rows in ablation files.
    final_methods = ["RandomResidualAudit", "StandardEnumerator", "SafeEnumerator",
                     "UpwardAudit", "DownwardAudit", "ShuffledSafeAudit"]
    out: dict[str, dict] = {}
    for reg in ("registry", "news", "active"):
        out[reg] = {}
        for method in final_methods:
            items = []
            for (row_reg, dataset, row_method, source), metrics in grouped.items():
                if row_reg != reg or row_method != method:
                    continue
                # For the final randomized audit, take only rows from final files.
                if method == "RandomResidualAudit":
                    matching = [r for r in rows if regime(r["dataset"]) == reg
                                and r["dataset"] == dataset
                                and r["source_id"] == source and r["stratum"] == "N"]
                    if not matching:
                        continue
                    metrics = defaultdict(list)
                    for r in matching:
                        metrics["detected"].append(float(r["detected_nonmonotone"]))
                        metrics["queries"].append(float(r["queries"]))
                        metrics["audit_queries"].append(float(r["audit_queries"]))
                        if r.get("witness_audit_query") is not None:
                            metrics["witness"].append(float(r["witness_audit_query"]))
                items.append({name: float(np.mean(vals)) for name, vals in metrics.items()})
            if not items:
                continue
            detection = np.array([item["detected"] for item in items])
            out[reg][method] = {
                "sources": len(items),
                "detection_recall": float(detection.mean()),
                "source_bootstrap95": bootstrap_mean(detection, rng, args.draws),
                "mean_queries": float(np.mean([item["queries"] for item in items])),
                "mean_audit_queries": float(np.mean([item.get("audit_queries", 0.0) for item in items])),
                "mean_witness_audit_query_detected": float(np.mean(
                    [item["witness"] for item in items if "witness" in item]
                )) if any("witness" in item for item in items) else None,
            }
        uniform = out[reg].get("RandomResidualAudit")
        standard = out[reg].get("StandardEnumerator")
        if uniform and standard:
            # Reconstruct paired source means from the two final sources.
            u = {}
            s = {}
            for (row_reg, dataset, method, source), metrics in grouped.items():
                if row_reg != reg:
                    continue
                if method == "StandardEnumerator":
                    s[(dataset, source)] = float(np.mean(metrics["detected"]))
            for dataset, source in s:
                matching = [r for r in rows if regime(r["dataset"]) == reg
                            and r["dataset"] == dataset
                            and r["source_id"] == source and r["stratum"] == "N"]
                if matching:
                    u[(dataset, source)] = float(np.mean(
                        [r["detected_nonmonotone"] for r in matching]))
            common = sorted(set(u) & set(s))
            diffs = np.array([u[x] - s[x] for x in common])
            out[reg]["uniform_minus_standard"] = {
                "sources": len(common), "mean": float(diffs.mean()),
                "source_bootstrap95": bootstrap_mean(diffs, rng, args.draws),
            }
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

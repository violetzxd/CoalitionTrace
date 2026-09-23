#!/usr/bin/env python3
"""Development-only, source-clustered comparison of residual-audit policies."""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def _read(patterns: list[str]) -> list[dict]:
    rows: list[dict] = []
    for pattern in patterns:
        for filename in glob.glob(pattern):
            rows.extend(
                json.loads(line)
                for line in Path(filename).read_text(encoding="utf-8").splitlines()
                if line
            )
    return rows


def _ci(values: np.ndarray, rng: np.random.Generator, draws: int) -> list[float]:
    if len(values) == 0:
        return [float("nan"), float("nan")]
    means = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=20000)
    args = parser.parse_args()
    rows = [r for r in _read(args.inputs) if r["stratum"] == "N"]
    rng = np.random.default_rng(20270920)

    # Average template variants and randomized seeds inside each source cluster.
    raw: dict[tuple[str, str, str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        cell = f'{row["dataset"]}:{row["model"]}'
        key = (cell, row["dataset"], row["source_id"], row["method"])
        raw[key]["detected"].append(float(row["detected_nonmonotone"]))
        raw[key]["queries"].append(float(row["queries"]))
        if row.get("witness_audit_query") is not None:
            raw[key]["witness"].append(float(row["witness_audit_query"]))

    clustered: dict[tuple[str, str], dict[str, float]] = {}
    for (cell, _dataset, source, method), metrics in raw.items():
        clustered[(f"{cell}|{source}", method)] = {
            name: float(np.mean(values)) for name, values in metrics.items()
        }

    methods = sorted({method for _, method in clustered})
    cells = sorted({cluster.split("|", 1)[0] for cluster, _ in clustered})
    output: dict[str, object] = {"development_only": True, "cells": {}, "pooled": {}}

    for cell in cells + ["POOLED"]:
        clusters = sorted({
            cluster for cluster, _ in clustered
            if cell == "POOLED" or cluster.startswith(cell + "|")
        })
        cell_out: dict[str, object] = {}
        for method in methods:
            available = [c for c in clusters if (c, method) in clustered]
            if not available:
                continue
            detection = np.array([clustered[(c, method)]["detected"] for c in available])
            queries = np.array([clustered[(c, method)]["queries"] for c in available])
            witness = [clustered[(c, method)]["witness"] for c in available
                       if "witness" in clustered[(c, method)]]
            cell_out[method] = {
                "clusters": len(available),
                "detection": float(detection.mean()),
                "detection_ci95": _ci(detection, rng, args.draws),
                "mean_queries": float(queries.mean()),
                "mean_witness_query_detected": float(np.mean(witness)) if witness else None,
            }
        for method in methods:
            if not method.startswith("EWRA-"):
                continue
            for baseline in ("RandomResidualAudit", "ShuffledSafeAudit"):
                common = [c for c in clusters
                          if (c, method) in clustered and (c, baseline) in clustered]
                if not common:
                    continue
                diffs = np.array([
                    clustered[(c, method)]["detected"]
                    - clustered[(c, baseline)]["detected"] for c in common
                ])
                cell_out[f"{method}_minus_{baseline}"] = {
                    "clusters": len(common), "mean": float(diffs.mean()),
                    "ci95": _ci(diffs, rng, args.draws),
                    "positive_cells_input": None,
                }
        if cell == "POOLED":
            output["pooled"] = cell_out
        else:
            output["cells"][cell] = cell_out

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

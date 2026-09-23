#!/usr/bin/env python3
"""Evaluate the randomized residual audit on the frozen stable-N subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


PAIRS = {
    "hotpot_qwen": "uan_hotpot_qwen_test",
    "nq_qwen": "uan_nq_qwen_test",
    "hotpot_mistral": "uan_hotpot_mistral_test",
    "nq_mistral": "uan_nq_mistral_test",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=10000)
    args = parser.parse_args()

    cases = []
    for cell, uniform_stem in PAIRS.items():
        stable = json.loads((args.results / f"stable_n_safe_{cell}.json").read_text())
        stable_ids = {row["case_id"] for row in stable["cases"] if row["stable_n"]}
        rows = [json.loads(line) for line in
                (args.results / f"uniform_{uniform_stem}.jsonl").read_text().splitlines() if line]
        for case_id in sorted(stable_ids):
            selected = [r for r in rows if r["case_id"] == case_id and r["stratum"] == "N"]
            cases.append({
                "cell": cell,
                "case_id": case_id,
                "seed_runs": len(selected),
                "detection_probability": float(np.mean(
                    [r["detected_nonmonotone"] for r in selected])),
            })
    # Cluster duplicate source IDs across generators by averaging before resampling.
    clusters: dict[str, list[float]] = {}
    for row in cases:
        source = row["case_id"].split(":", 4)[-1]
        clusters.setdefault(source, []).append(row["detection_probability"])
    values = np.array([np.mean(v) for v in clusters.values()])
    rng = np.random.default_rng(202709)
    boot = rng.choice(values, size=(args.draws, len(values)), replace=True).mean(axis=1)
    output = {
        "stable_model_cases": len(cases),
        "source_clusters": len(values),
        "ten_seed_mean_recall": float(values.mean()),
        "source_cluster_bootstrap95": [float(x) for x in np.quantile(boot, [0.025, 0.975])],
        "cases": cases,
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

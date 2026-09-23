#!/usr/bin/env python3
"""Aggregate post-hoc SafeEnumerator transfer experiments."""

from __future__ import annotations

import argparse
import glob
import json
import math
from collections import defaultdict
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [center - half, center + half]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", dest="patterns", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = sorted({p for pattern in args.patterns for p in glob.glob(pattern)})
    cells = []
    pooled = defaultdict(lambda: [0, 0])
    for raw_path in paths:
        path = Path(raw_path)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        n_rows = [row for row in rows if row["stratum"] == "N"]
        a_rows = [row for row in rows if row["stratum"] == "A"]
        detected = sum(bool(row["detected_nonmonotone"]) for row in n_rows)
        regime = "news" if "_news_" in path.name else "active"
        pooled[regime][0] += detected
        pooled[regime][1] += len(n_rows)
        cells.append({
            "file": path.name,
            "regime": regime,
            "n_detected": detected,
            "n_total": len(n_rows),
            "n_recall": detected / len(n_rows),
            "n_wilson95": wilson(detected, len(n_rows)),
            "a_total": len(a_rows),
            "a_acem": sum(row["acem"] for row in a_rows) / len(a_rows) if a_rows else None,
            "mean_unique_prompts": sum(row["queries"] for row in rows) / len(rows),
        })
    result = {"cells": cells, "pooled": {}}
    for regime, (detected, total) in pooled.items():
        result["pooled"][regime] = {
            "n_detected": detected,
            "n_total": total,
            "n_recall": detected / total,
            "n_wilson95": wilson(detected, total),
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

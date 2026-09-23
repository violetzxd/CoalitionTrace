#!/usr/bin/env python3
"""Plot the accuracy--safety frontier for the residual-budget audit."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--jsonl-glob")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.jsonl_glob:
        raw = [json.loads(line) for path in glob.glob(args.jsonl_glob)
               for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
        cells: dict[tuple[str, str, str, int], list[float]] = {}
        for row in raw:
            metric = "acem" if row["stratum"] == "A" else "detected_nonmonotone"
            if row["stratum"] not in {"A", "N"}:
                continue
            key = (row["dataset"], row["model"], row["stratum"], row["budget"])
            cells.setdefault(key, []).append(float(row[metric]))
        rows = [
            {"dataset": d, "model": m, "stratum": s, "budget": b,
             "acem": float(np.mean(v)) if s == "A" else 0.0,
             "n_detection": float(np.mean(v)) if s == "N" else 0.0}
            for (d, m, s, b), v in cells.items()
        ]
    elif args.input:
        rows = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        parser.error("one of --input or --jsonl-glob is required")
    budgets = sorted({int(r["budget"]) for r in rows})
    a = {b: [r["acem"] for r in rows if r["stratum"] == "A" and r["budget"] == b] for b in budgets}
    n = {b: [r["n_detection"] for r in rows if r["stratum"] == "N" and r["budget"] == b] for b in budgets}

    mpl.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, ax = plt.subplots(figsize=(3.35, 1.75))
    for values, label, marker, linestyle, color in [
        (a, "A: all-cause ACEM", "o", "-", "#0072B2"),
        (n, "N: violation recall", "s", "--", "#D55E00"),
    ]:
        means = np.array([np.mean(values[b]) for b in budgets])
        lows = np.array([np.min(values[b]) for b in budgets])
        highs = np.array([np.max(values[b]) for b in budgets])
        ax.fill_between(budgets, lows, highs, color=color, alpha=0.12, linewidth=0)
        ax.plot(budgets, means, color=color, marker=marker, linestyle=linestyle,
                linewidth=1.5, markersize=4.2, label=label, zorder=3)
    ax.axhline(0.8, color="0.3", linewidth=0.9, linestyle=":", label="audit target")
    ax.set(xlabel="Unique-prompt budget", ylabel="Mean score", ylim=(0.25, 1.03), xticks=budgets)
    ax.grid(axis="y", color="0.9", linewidth=0.6)
    ax.legend(frameon=False, fontsize=7.1, loc="lower center",
              bbox_to_anchor=(0.5, 1.01), ncol=2, handlelength=2.0,
              columnspacing=.8)
    fig.subplots_adjust(left=.16, right=.985, bottom=.25, top=.72)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight", pad_inches=.02)


if __name__ == "__main__":
    main()

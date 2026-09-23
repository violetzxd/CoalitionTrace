from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


COLORS = {"AmbiCause": "#0072B2", "RepeatedGreedy": "#E69F00", "RandomMasks": "#009E73"}
LABELS = {"AmbiCause": "Adapt", "RepeatedGreedy": "Repeated", "RandomMasks": "Random"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accounting", type=Path, required=True)
    parser.add_argument("--registry-summary", type=Path, required=True)
    parser.add_argument("--active-summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    accounting = json.loads(args.accounting.read_text(encoding="utf-8"))["cells"]
    summary = json.loads(args.registry_summary.read_text(encoding="utf-8"))
    active = (json.loads(args.active_summary.read_text(encoding="utf-8"))
              if args.active_summary else [])

    plt.rcParams.update({
        "font.family": "serif", "font.size": 9,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.05))
    ax = axes[0]
    conditions, values = [], {method: [] for method in COLORS}
    for cell in accounting:
        short = "Hotpot" if "hotpot" in cell["cell"].lower() else "NQ"
        for regime, label in (("old", "mask"), ("fair", "prompt")):
            conditions.append(f"{short}\n{label}")
            for method in COLORS:
                values[method].append(cell[regime][method]["acem"])
    x = np.arange(len(conditions))
    width = 0.24
    handles = []
    for offset, method, hatch in zip((-width, 0, width), COLORS, ("//", "..", "xx")):
        bars = ax.bar(x + offset, values[method], width, color=COLORS[method],
                      edgecolor="black", linewidth=.35, hatch=hatch,
                      label=LABELS[method], zorder=3)
        handles.append(bars)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("A-stratum ACEM")
    ax.set_xticks(x, conditions)
    ax.set_title("(a) Accounting correction (Qwen)", loc="left", fontsize=9)
    ax.grid(axis="y", color="0.88", linewidth=.55, zorder=0)

    rows = [row for row in summary if row["budget"] == 48 and row["stratum"] == "A"
            and row["method"] == "AmbiCause"]
    active_rows = [row for row in active if row["budget"] == 48 and row["stratum"] == "A"
                   and row["method"] == "AmbiCause"]
    labels, fractions = [], []
    for row in rows + active_rows:
        dataset = "Hotpot" if "hotpot" in row["dataset"].lower() else "NQ"
        model = "Q" if "qwen" in row["model"].lower() else "M"
        suffix = "-active" if row in active_rows else ""
        labels.append(f"{dataset[:1]}-{model}{'*' if suffix else ''}")
        fractions.append(row["oracle_unique_prompts"] / row["oracle_total_masks"])
    ax = axes[1]
    bars = ax.bar(np.arange(len(labels)), fractions, color=["#56B4E9"] * len(rows)
                  + ["#CC79A7"] * len(active_rows), edgecolor="black", linewidth=.35,
                  zorder=3)
    for bar in bars[len(rows):]:
        bar.set_hatch("//")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel(r"$|\mathcal{Q}|/2^n$")
    ax.set_xticks(np.arange(len(labels)), labels, rotation=0, fontsize=8)
    ax.set_title("(b) Effective intervention space", loc="left", fontsize=9)
    ax.grid(axis="y", color="0.88", linewidth=.55, zorder=0)
    for bar, value in zip(bars, fractions):
        ax.text(bar.get_x() + bar.get_width()/2, value + .025, f"{value:.2f}",
                ha="center", va="bottom", fontsize=7.2)

    from matplotlib.patches import Patch
    method_handles = [h[0] for h in handles]
    regime_handles = [
        Patch(facecolor="#56B4E9", edgecolor="black", label="Registry"),
        Patch(facecolor="#CC79A7", edgecolor="black", hatch="//", label="All-active (*)"),
    ]
    fig.legend(method_handles + regime_handles,
               [LABELS[m] for m in COLORS] + ["Registry", "All-active (*)"],
               loc="upper center", bbox_to_anchor=(0.5, 1.01), ncol=5,
               frameon=False, fontsize=8, handlelength=1.6, columnspacing=1.0)
    fig.subplots_adjust(left=.075, right=.995, bottom=.27, top=.78, wspace=.28)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight", pad_inches=.02)
    print(args.output)


if __name__ == "__main__":
    main()

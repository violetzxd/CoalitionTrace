#!/usr/bin/env python3
"""Create a compact vector overview of the CoalitionTrace decision pipeline."""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


def box(ax, x, y, w, h, title, body, color):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=0.8, edgecolor="#333333", facecolor=color,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * .69, title, ha="center", va="center",
            fontsize=7.0, fontweight="bold", clip_on=True)
    ax.text(x + w / 2, y + h * .30, body, ha="center", va="center",
            fontsize=5.75, linespacing=1.04, clip_on=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plt.rcParams.update({"font.family": "serif", "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(7.0, 1.48))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    xs = [.014, .212, .410, .608, .806]
    w, h, y = .18, .54, .26
    items = [
        ("1. Validate", "Replay empty + full\ninvalid: out of scope", "#E8F1F8"),
        ("2. LOO test", "Delete each document\nform backbone B", "#D8EBF6"),
        ("3. Cause search", "Protect enumeration\nexhaust its frontier", "#E7F3E5"),
        ("4. Safety audit", "Sample unseen classes\nstop at a reversal", "#FFF0D6"),
        ("5. Grade output", "Causes + witness + cost\ncertify or abstain", "#F5E4EC"),
    ]
    for i, (title, body, color) in enumerate(items):
        box(ax, xs[i], y, w, h, title, body, color)
        if i < len(items) - 1:
            ax.add_patch(FancyArrowPatch(
                (xs[i] + w + .006, y + h / 2), (xs[i + 1] - .006, y + h / 2),
                arrowstyle="-|>", mutation_scale=10, linewidth=1.0, color="#444444",
            ))
    ax.text(.5, .94, "Enumerate first; audit only with the residual physical-call budget",
            ha="center", va="center", fontsize=8.1, fontweight="bold")
    ax.text(.5, .075,
            "A found reversal rejects monotonicity; an unviolated non-exhaustive trace remains inconclusive.",
            ha="center", va="center", fontsize=7.3, style="italic")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight", pad_inches=.02)


if __name__ == "__main__":
    main()

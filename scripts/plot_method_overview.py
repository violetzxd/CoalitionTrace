#!/usr/bin/env python3
"""Create the camera-ready vector overview of the CoalitionTrace pipeline."""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


INK = "#213245"
MUTED = "#607080"
LINE = "#8090A0"
BLUE = "#DCECF8"
GREEN = "#E2F2E5"
AMBER = "#FFF0D2"
ROSE = "#F5E2EB"
SLATE = "#EEF2F5"
WHITE = "#FFFFFF"


def box(ax, xy, size, facecolor, linewidth=0.9, radius=0.018):
    x, y = xy
    w, h = size
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        linewidth=linewidth, edgecolor=INK, facecolor=facecolor,
    )
    ax.add_patch(patch)
    return patch


def stage_card(ax, x, color, number, title, line1, line2):
    """Draw one fixed-width stage card with explicit line breaks."""
    y, w, h = 0.350, 0.218, 0.330
    patch = box(ax, (x, y), (w, h), WHITE, radius=0.020)
    ax.add_patch(FancyBboxPatch(
        (x + 0.006, y + h - 0.105), w - 0.012, 0.095,
        boxstyle="round,pad=0.004,rounding_size=0.014",
        linewidth=0, facecolor=color,
    ))
    ax.text(x + 0.018, y + h - 0.058, f"{number}  {title}",
            ha="left", va="center", fontsize=9.4,
            fontweight="bold", color=INK)
    ax.text(x + w / 2, y + 0.150, line1,
            ha="center", va="center", fontsize=9.0, color=INK)
    ax.text(x + w / 2, y + 0.072, line2,
            ha="center", va="center", fontsize=9.0, color=MUTED)
    return patch


def arrow(ax, start, end, color=INK, lw=1.0):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=10,
        linewidth=lw, color=color, shrinkA=1, shrinkB=1,
    ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plt.rcParams.update({
        "font.family": "serif",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, ax = plt.subplots(figsize=(7.08, 2.48))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Layer 1: freeze the causal object before any attribution query.
    box(ax, (0.018, 0.810), (0.964, 0.140), SLATE, radius=0.020)
    ax.text(0.042, 0.880, "Frozen replay contract", ha="left", va="center",
            fontsize=9.5, fontweight="bold", color=INK)
    ax.text(0.365, 0.880,
            r"$D,\ \widetilde{D},\ y_t,\ g,\ r,$ and $\tau$ remain fixed before attribution",
            ha="left", va="center", fontsize=9.0, color=INK)

    # Layer 2: the four-stage inference path.
    xs = [0.018, 0.265, 0.512, 0.759]
    stage_card(ax, xs[0], BLUE, "1", "Diagnose",
               "LOO boundary", r"$\emptyset, D, D_{-i}$ queries")
    stage_card(ax, xs[1], GREEN, "2", "Enumerate",
               r"frontier $F$", "verify minimality")
    stage_card(ax, xs[2], AMBER, "3", "Audit",
               "unseen prompts", "find a witness")
    stage_card(ax, xs[3], ROSE, "4", "Grade",
               "causes + coverage", "witness / abstain")
    for left, right in zip(xs[:-1], xs[1:]):
        arrow(ax, (left + 0.220, 0.625), (right - 0.003, 0.625))

    # The contract governs the whole path without crossing the stage arrows.
    ax.plot([0.500, 0.500], [0.810, 0.750], color=INK, linewidth=0.9)
    ax.plot([0.127, 0.873], [0.750, 0.750], color=INK, linewidth=0.9)
    for x in (0.127, 0.374, 0.621, 0.868):
        arrow(ax, (x, 0.750), (x, 0.690), lw=0.9)

    ax.text(0.500, 0.280,
            "Budget invariant: enumerate first; audit with residual physical calls",
            ha="center", va="center", fontsize=9.0,
            fontweight="bold", color=INK)

    # Layer 3: shared state and the two principal design advantages.
    box(ax, (0.018, 0.055), (0.470, 0.150), BLUE, radius=0.020)
    ax.text(0.040, 0.148, r"Exact-prompt cache $H$", ha="left", va="center",
            fontsize=9.3, fontweight="bold", color=INK)
    ax.text(0.040, 0.092, "one charged call per prompt class",
            ha="left", va="center", fontsize=9.0, color=MUTED)

    box(ax, (0.512, 0.055), (0.470, 0.150), GREEN, radius=0.020)
    ax.text(0.534, 0.148, "Auditable evidence ledger", ha="left", va="center",
            fontsize=9.3, fontweight="bold", color=INK)
    ax.text(0.534, 0.092, "prompt ID  |  cost  |  causes  |  witness",
            ha="left", va="center", fontsize=9.0, color=MUTED)

    ax.plot([0.253, 0.253], [0.213, 0.240], color=LINE, linewidth=0.8)
    ax.plot([0.747, 0.747], [0.213, 0.240], color=LINE, linewidth=0.8)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)


if __name__ == "__main__":
    main()

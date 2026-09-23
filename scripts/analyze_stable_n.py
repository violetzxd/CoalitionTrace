from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 1.0]
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return [center - radius, center + radius]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--margins", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path)
    parser.add_argument("--order-analysis", type=Path)
    parser.add_argument("--replacement-analysis", type=Path)
    parser.add_argument("--budget", type=int, default=48)
    parser.add_argument("--method", default="AmbiCause")
    parser.add_argument("--delta", type=float, default=0.25)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selected = {
        row["case_id"] for row in map(json.loads, args.selection.open(encoding="utf-8"))
        if row["stratum"] == "N"
    }
    values = defaultdict(dict)
    ns = {}
    for row in map(json.loads, args.oracle.open(encoding="utf-8")):
        if row["case_id"] in selected:
            values[row["case_id"]][int(row["mask"])] = float(row["utility"])
            ns[row["case_id"]] = int(row["n"])
    margins = {}
    for row in map(json.loads, args.margins.open(encoding="utf-8")):
        for mask in row.get("equivalent_masks", [row["mask"]]):
            margins[(row["case_id"], int(mask))] = float(row["target_correct_margin"])

    detected = {}
    if args.evaluation:
        for row in map(json.loads, args.evaluation.open(encoding="utf-8")):
            if (row["budget"] == args.budget and row["method"] == args.method
                    and row["seed"] == 0):
                detected[row["case_id"]] = bool(row["detected_nonmonotone"])

    def load_variant_labels(path: Path | None, suffix: str) -> dict[str, str]:
        if path is None:
            return {}
        labels = {}
        for row in map(json.loads, path.open(encoding="utf-8")):
            case_id = row["case_id"]
            if not case_id.endswith(suffix):
                raise ValueError(f"unexpected variant id {case_id!r}; expected suffix {suffix!r}")
            labels[case_id.removesuffix(suffix)] = row["stratum"]
        return labels

    order_labels = load_variant_labels(args.order_analysis, ":order2")
    replacement_labels = load_variant_labels(args.replacement_analysis, ":replacement2")
    require_variants = args.order_analysis is not None or args.replacement_analysis is not None
    if require_variants and (args.order_analysis is None or args.replacement_analysis is None):
        raise ValueError("order and replacement analyses must be supplied together")

    cases = []
    for case_id in sorted(selected):
        violations = []
        stable = []
        full = (1 << ns[case_id]) - 1
        for lower, value in values[case_id].items():
            if value < 1.0:
                continue
            remaining = full & ~lower
            while remaining:
                bit = remaining & -remaining
                upper = lower | bit
                if values[case_id][upper] < 1.0:
                    violations.append((lower, upper))
                    if (margins.get((case_id, lower), float("-inf")) >= args.delta
                            and margins.get((case_id, upper), float("inf")) <= -args.delta):
                        stable.append((lower, upper))
                remaining -= bit
        margin_stable = bool(stable)
        order_n = order_labels.get(case_id) == "N" if require_variants else None
        replacement_n = replacement_labels.get(case_id) == "N" if require_variants else None
        stable_n = margin_stable and (not require_variants or (order_n and replacement_n))
        cases.append({
            "case_id": case_id,
            "raw_violation_edges": len(violations),
            "margin_stable_edges": len(stable),
            "margin_stable_n": margin_stable,
            "order_variant_n": order_n,
            "replacement_variant_n": replacement_n,
            "stable_n": stable_n,
            "detected_nonmonotone": detected.get(case_id),
        })
    stable_cases = [row for row in cases if row["stable_n"]]
    detected_stable = sum(bool(row["detected_nonmonotone"]) for row in stable_cases)
    payload = {
        "delta_mean_logprob_nats": args.delta,
        "requires_order_and_replacement_stability": require_variants,
        "raw_n": len(cases),
        "stable_n": len(stable_cases),
        "stable_rate": len(stable_cases) / len(cases) if cases else 0.0,
        "stable_rate_ci95_wilson": wilson(len(stable_cases), len(cases)),
        "method": args.method,
        "budget": args.budget,
        "detected_stable_n": detected_stable,
        "stable_n_detection_recall": detected_stable / len(stable_cases) if stable_cases else None,
        "stable_n_detection_ci95_wilson": wilson(detected_stable, len(stable_cases)),
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "cases"}, indent=2))


if __name__ == "__main__":
    main()

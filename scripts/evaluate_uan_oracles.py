from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from coalitiontrace.ambicause import ambicause
from coalitiontrace.baselines import ddmin, kernel_shap
from coalitiontrace.core import UtilityTable
from coalitiontrace.set_baselines import (
    downward_audited_enumerator, exposure_weighted_audited_enumerator,
    exposed_random_audited_enumerator, loo_set, random_mask_enumerator,
    hybrid_residual_audited_enumerator,
    random_residual_audited_enumerator, repeated_greedy,
    safety_audited_enumerator, shuffled_safety_audited_enumerator,
    standard_monotone_enumerator, upward_audited_enumerator,
)


def scores(predicted: tuple[int, ...], truth: tuple[int, ...]) -> dict[str, float]:
    p, t = set(predicted), set(truth)
    matched = len(p & t)
    precision = matched / len(p) if p else float(not t)
    recall = matched / len(t) if t else float(not p)
    return {
        "acem": float(p == t), "any_cause": float(bool(p & t)),
        "cause_precision": precision, "cause_recall": recall,
        "cause_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "false_cause": float(bool(p - t)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budgets", type=int, nargs="+", default=[16, 32, 64, 128])
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--dataset", default="unknown")
    parser.add_argument("--model", default="unknown")
    parser.add_argument("--methods", nargs="+", help="Optional method-name subset")
    args = parser.parse_args()
    grouped = defaultdict(dict)
    query_keys = defaultdict(dict)
    token_costs = defaultdict(dict)
    for line in args.oracle.open(encoding="utf-8"):
        row = json.loads(line)
        grouped[row["case_id"]][int(row["mask"])] = float(row["utility"])
        query_keys[row["case_id"]][int(row["mask"])] = row.get(
            "prompt_sha256", int(row["mask"])
        )
        key = query_keys[row["case_id"]][int(row["mask"])]
        token_costs[row["case_id"]][key] = (
            int(row.get("input_tokens", 0)), int(row.get("output_tokens", 0))
        )
    labels = {r["case_id"]: r for r in map(json.loads, args.analysis.open(encoding="utf-8"))}
    selected = None
    sources = {}
    if args.selection:
        selection_rows = list(map(json.loads, args.selection.open(encoding="utf-8")))
        selected = {row["case_id"] for row in selection_rows}
        sources = {row["case_id"]: row["source_id"] for row in selection_rows}
    rows = []
    for case_id, values in grouped.items():
        if case_id not in labels or (selected is not None and case_id not in selected):
            continue
        label = labels[case_id]
        n = int(round(len(values).bit_length() - 1))
        table = UtilityTable(n, values, query_keys=query_keys[case_id])
        truth = tuple(label["minima"])
        for budget in args.budgets:
            deterministic = {}
            deterministic_runners = {
                "AmbiCause": lambda t: ambicause(t, budget, general_fallback=False),
                "AmbiCauseAudit": lambda t: ambicause(
                    t, budget, general_fallback=False, audit_upward=True
                ),
                "LOO": lambda t: loo_set(t, budget),
                "StandardEnumerator": lambda t: standard_monotone_enumerator(t, budget),
                "SafeEnumerator": lambda t: safety_audited_enumerator(t, budget),
                "UpwardAudit": lambda t: upward_audited_enumerator(t, budget),
                "DownwardAudit": lambda t: downward_audited_enumerator(t, budget),
            }
            if args.methods:
                deterministic_runners = {
                    name: runner for name, runner in deterministic_runners.items()
                    if name in args.methods
                }
            for method, runner in deterministic_runners.items():
                method_table = table.fork()
                deterministic[method] = (runner(method_table), method_table)
            if not args.methods or "HierarchicalDeletion" in args.methods:
                deletion_table = table.fork()
                deletion = ddmin(deletion_table, budget)
                deterministic["HierarchicalDeletion"] = (type(
                    "Result", (), {"causes": (() if deletion.mask is None else (deletion.mask,)),
                                    "queries": deletion.queries})(), deletion_table)
            for method, (result, method_table) in deterministic.items():
                used_keys = {method_table.query_key(mask) for mask in method_table.queries}
                rows.append({"case_id": case_id, "source_id": sources.get(case_id, case_id),
                             "dataset": args.dataset, "model": args.model,
                             "family": label["family"],
                             "stratum": label["stratum"], "budget": budget,
                             "seed": 0, "method": method, "queries": result.queries,
                             "mask_queries": method_table.unique_masks,
                             "input_tokens": sum(token_costs[case_id][key][0] for key in used_keys),
                             "output_tokens": sum(token_costs[case_id][key][1] for key in used_keys),
                             "oracle_unique_prompts": len(set(query_keys[case_id].values())),
                             "oracle_total_masks": len(values),
                             "detected_nonmonotone": bool(
                                 getattr(result, "observed_violation", None)),
                             "conditional_complete": bool(
                                 getattr(result, "complete_claim", False)),
                             "unconditional_complete": False,
                             "quotient_exhausted": bool(
                                 getattr(result, "quotient_exhausted", False)),
                             "audit_status": (
                                 "violation_found" if getattr(result, "observed_violation", None)
                                 else "quotient_exhausted_no_violation"
                                 if getattr(result, "quotient_exhausted", False)
                                 else "inconclusive"),
                             "enumeration_queries": getattr(
                                 result, "enumeration_queries", None),
                             "audit_queries": (
                                 result.queries - result.enumeration_queries
                                 if getattr(result, "enumeration_queries", None) is not None
                                 else None),
                             "witness_audit_query": getattr(
                                 result, "witness_audit_query", None),
                             "audit_trace": getattr(result, "audit_trace", ()),
                             **scores(result.causes, truth)})
            stochastic_names = {
                "RepeatedGreedy", "RandomMasks", "KernelSHAP",
                "RandomResidualAudit", "ShuffledSafeAudit",
                "ExposedRandomAudit", "EWRA-Balanced", "EWRA-Raw",
                "EWRA-Normalized", "EWRA-Maximin", "EWRA-Sparse",
                "EWRA-Nearest", "Hybrid25", "Hybrid50", "Hybrid75",
            }
            for seed in range(args.seeds if not args.methods or stochastic_names & set(args.methods) else 0):
                stochastic = {}
                stochastic_runners = {
                    "RepeatedGreedy": lambda t: repeated_greedy(t, budget, seed=seed),
                    "RandomMasks": lambda t: random_mask_enumerator(t, budget, seed=seed),
                    "KernelSHAP": lambda t: kernel_shap(t, budget, seed=seed),
                    "RandomResidualAudit": lambda t: random_residual_audited_enumerator(
                        t, budget, seed=seed),
                    "ShuffledSafeAudit": lambda t: shuffled_safety_audited_enumerator(
                        t, budget, seed=seed),
                    "ExposedRandomAudit": lambda t: exposed_random_audited_enumerator(
                        t, budget, seed=seed),
                    "EWRA-Balanced": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="balanced"),
                    "EWRA-Raw": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="raw"),
                    "EWRA-Normalized": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="normalized"),
                    "EWRA-Maximin": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="maximin"),
                    "EWRA-Sparse": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="sparse"),
                    "EWRA-Nearest": lambda t: exposure_weighted_audited_enumerator(
                        t, budget, seed=seed, variant="nearest"),
                    "Hybrid25": lambda t: hybrid_residual_audited_enumerator(
                        t, budget, seed=seed, boundary_percent=25),
                    "Hybrid50": lambda t: hybrid_residual_audited_enumerator(
                        t, budget, seed=seed, boundary_percent=50),
                    "Hybrid75": lambda t: hybrid_residual_audited_enumerator(
                        t, budget, seed=seed, boundary_percent=75),
                }
                if args.methods:
                    stochastic_runners = {
                        name: runner for name, runner in stochastic_runners.items()
                        if name in args.methods
                    }
                for method, runner in stochastic_runners.items():
                    method_table = table.fork()
                    result = runner(method_table)
                    if method == "KernelSHAP":
                        result = type("Result", (), {
                            "causes": (() if result.mask is None else (result.mask,)),
                            "queries": result.queries,
                        })()
                    stochastic[method] = (result, method_table)
                for method, (result, method_table) in stochastic.items():
                    used_keys = {method_table.query_key(mask) for mask in method_table.queries}
                    rows.append({"case_id": case_id, "source_id": sources.get(case_id, case_id),
                                 "dataset": args.dataset, "model": args.model,
                                 "family": label["family"],
                                 "stratum": label["stratum"], "budget": budget,
                                 "seed": seed, "method": method, "queries": result.queries,
                                 "mask_queries": method_table.unique_masks,
                                 "input_tokens": sum(token_costs[case_id][key][0] for key in used_keys),
                                 "output_tokens": sum(token_costs[case_id][key][1] for key in used_keys),
                                 "oracle_unique_prompts": len(set(query_keys[case_id].values())),
                                 "oracle_total_masks": len(values),
                                 "detected_nonmonotone": bool(
                                     getattr(result, "observed_violation", None)),
                                 "conditional_complete": bool(
                                     getattr(result, "complete_claim", False)),
                                 "unconditional_complete": False,
                                 "quotient_exhausted": bool(
                                     getattr(result, "quotient_exhausted", False)),
                                 "audit_status": (
                                     "violation_found" if getattr(result, "observed_violation", None)
                                     else "quotient_exhausted_no_violation"
                                     if getattr(result, "quotient_exhausted", False)
                                     else "inconclusive"),
                                 "enumeration_queries": getattr(
                                     result, "enumeration_queries", None),
                                 "audit_queries": (
                                     result.queries - result.enumeration_queries
                                     if getattr(result, "enumeration_queries", None) is not None
                                     else None),
                                 "witness_audit_query": getattr(
                                     result, "witness_audit_query", None),
                                 "audit_trace": getattr(result, "audit_trace", ()),
                                 **scores(result.causes, truth)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()

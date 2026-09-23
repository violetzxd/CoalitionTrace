#!/usr/bin/env python3
"""Non-selective audit of every stored oracle-screening analysis artifact."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

import numpy as np


STRATA = ("U", "A", "N", "OOS")


def source_id(row: dict) -> str | None:
    """Recover the base dataset/source cluster from frozen case identifiers."""
    if row.get("source_id"):
        return str(row["source_id"])
    case_id, family = str(row.get("case_id", "")), str(row.get("family", ""))
    if case_id.startswith(family + ":"):
        value = case_id[len(family) + 1:]
    elif case_id.startswith("holdout-v1:") and case_id.startswith(family + ":"):
        value = case_id[len(family) + 1:]
    else:
        match = re.search(r":v\d+:(.+)$", case_id)
        if not match:
            return None
        value = match.group(1)
    return re.sub(r":(order2|replacement2)$", "", value)


def cluster_interval(rows: list[dict], indicator, seed_key: str,
                     draws: int = 20_000) -> list[float] | None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source = source_id(row)
        if source is None:
            return None
        grouped[source].append(row)
    if len(grouped) < 2:
        return None
    clusters = sorted(grouped)
    numerator = np.asarray([sum(indicator(row) for row in grouped[key])
                            for key in clusters], dtype=float)
    denominator = np.asarray([len(grouped[key]) for key in clusters], dtype=float)
    seed = int(hashlib.sha256(seed_key.encode()).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(clusters), size=(draws, len(clusters)))
    values = numerator[sampled].sum(axis=1) / denominator[sampled].sum(axis=1)
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line]


def pair_key(name: str) -> str:
    return re.sub(r"_(qwen|mistral)(?=_|$)", "_MODEL", name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--confirmatory2-gate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    files = sorted(args.results.glob("*analysis*.jsonl"))
    artifacts = {}
    rows_by_file = {}
    for path in files:
        rows = read_jsonl(path)
        rows_by_file[path.name] = rows
        counts = Counter(str(row.get("stratum", "INVALID")) for row in rows)
        n = len(rows)
        sources = {source_id(row) for row in rows}
        recoverable = None not in sources
        artifacts[path.name] = {
            "complete_tables": n,
            "source_clusters": len(sources) if recoverable else None,
            "inference": ("source_cluster_bootstrap_20000"
                          if recoverable and len(sources) >= 2
                          else "descriptive_only_unresolved_or_single_source"),
            "strata": {key: counts.get(key, 0) for key in (*STRATA, "INVALID")},
            "rates": {
                key: {"point": counts.get(key, 0) / n if n else None,
                      "source_cluster_bootstrap95": cluster_interval(
                          rows, lambda row, target=key: row.get("stratum") == target,
                          f"artifact|{path.name}|{key}")}
                for key in STRATA
            },
        }

    paired = {}
    groups = {}
    for name in rows_by_file:
        groups.setdefault(pair_key(name), []).append(name)
    for key, names in sorted(groups.items()):
        qwen = next((name for name in names if "_qwen" in name), None)
        mistral = next((name for name in names if "_mistral" in name), None)
        if not qwen or not mistral:
            continue
        left = {str(row["case_id"]): str(row.get("stratum", "INVALID"))
                for row in rows_by_file[qwen]}
        right = {str(row["case_id"]): str(row.get("stratum", "INVALID"))
                 for row in rows_by_file[mistral]}
        common = sorted(set(left) & set(right))
        agree = sum(left[case_id] == right[case_id] for case_id in common)
        metadata = {str(row["case_id"]): row for row in rows_by_file[qwen]}
        paired_rows = [
            {**metadata[case_id], "agree": left[case_id] == right[case_id]}
            for case_id in common
        ]
        agreement_interval = cluster_interval(
            paired_rows, lambda row: bool(row["agree"]), f"agreement|{key}"
        )
        recovered = {source_id(row) for row in paired_rows}
        paired[key] = {
            "qwen_file": qwen, "mistral_file": mistral,
            "common_cases": len(common), "same_stratum": agree,
            "source_clusters": len(recovered) if None not in recovered else None,
            "agreement": agree / len(common) if common else None,
            "source_cluster_bootstrap95": agreement_interval,
            "inference": ("source_cluster_bootstrap_20000"
                          if agreement_interval is not None
                          else "descriptive_only_unresolved_or_single_source"),
        }

    output = {
        "scope": ("retrospective, non-selective inventory of all analysis JSONL "
                  "artifacts; no family or outcome filtering; no cross-artifact pooling"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "cross_model_agreement": paired,
    }
    if args.confirmatory2_gate:
        output["confirmatory2_feasibility_only"] = json.loads(
            args.confirmatory2_gate.read_text(encoding="utf-8")
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact_count": len(artifacts),
                      "paired_comparisons": len(paired)}))


if __name__ == "__main__":
    main()

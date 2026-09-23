from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from coalitiontrace.core import CoalitionCase


def sha256(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output-ids", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    cases = [CoalitionCase.from_json(json.loads(line))
             for line in args.cases.open(encoding="utf-8")]
    labels = {row["case_id"]: row for row in
              map(json.loads, args.analysis.open(encoding="utf-8"))}
    by_source: dict[str, list[CoalitionCase]] = defaultdict(list)
    for case in cases:
        by_source[case.source_id].append(case)
    selected = []
    yields = Counter()
    planted_to_realized = Counter()
    for source_id, candidates in by_source.items():
        for case in candidates:
            if case.case_id in labels:
                planted_to_realized[(case.planted_stratum, labels[case.case_id]["stratum"])] += 1
        for stratum in ("U", "A", "N"):
            match = next((case for case in candidates
                          if case.case_id in labels and labels[case.case_id]["stratum"] == stratum), None)
            if match is not None:
                selected.append({"source_id": source_id, "stratum": stratum,
                                 "case_id": match.case_id})
                yields[stratum] += 1
    args.output_ids.parent.mkdir(parents=True, exist_ok=True)
    with args.output_ids.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row) + "\n")
    manifest = {
        "source_queries": len(by_source), "candidate_cases": len(cases),
        "complete_oracle_cases": len(labels), "selected": dict(yields),
        "planted_to_realized": {f"{a}->{b}": count
                                for (a, b), count in sorted(planted_to_realized.items())},
        "cases_sha256": sha256(args.cases), "analysis_sha256": sha256(args.analysis),
        "rule": "first candidate in frozen file order with requested oracle stratum; method-blind",
    }
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

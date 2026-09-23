from __future__ import annotations

import argparse
import json
from pathlib import Path

from coalitiontrace.benchmark import read_jsonl
from coalitiontrace.benchmark_uan import make_uan_case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--n", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--profile", choices=["balanced", "confirmatory", "screening", "a_only"],
        default="balanced",
    )
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--style", choices=["registry", "news"], default="registry")
    parser.add_argument("--all-active", action="store_true")
    args = parser.parse_args()
    rows = list(read_jsonl(args.input))
    if args.split != "all":
        rows = [row for row in rows if row.get("split") == args.split]
    if args.limit:
        rows = rows[:args.limit]
    balanced = [
        ("U", 2, False), ("U", 3, False),
        ("A", 2, False), ("A", 2, True),
        ("A", 3, False), ("A", 3, True),
        ("N", 2, False),
    ]
    # Frozen after the R3 development pilot. This profile increases yield without
    # selecting on method success: both models retained, every generated/excluded
    # case remains in the construction funnel.
    confirmatory = [
        ("U", 2, False), ("U", 3, False),
        ("A", 2, False), ("A", 2, False), ("A", 2, False),
        ("A", 3, False), ("A", 3, True),
        ("N", 2, False),
    ]
    screening = [
        ("U", 2, False), ("U", 3, False),
        ("A", 2, False), ("A", 2, False), ("A", 2, True),
        ("A", 3, False), ("A", 3, True), ("N", 2, False),
    ]
    a_only = [
        ("A", 2, False), ("A", 2, False), ("A", 2, True),
        ("A", 3, False), ("A", 3, True),
    ]
    configs = {"balanced": balanced, "confirmatory": confirmatory,
               "screening": screening, "a_only": a_only}[args.profile]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows):
            donors = []
            for offset in range(1, len(rows)):
                donor = rows[(index + offset) % len(rows)]
                if donor["id"] == row["id"]:
                    continue
                donors.extend(str(doc["text"]) for doc in donor.get("documents", []))
                if len(donors) >= 2 * args.n:
                    break
            chosen = configs if args.profile in {"screening", "a_only"} else [
                configs[index % len(configs)]
            ]
            for local_variant, (stratum, size, overlap) in enumerate(chosen):
                case = make_uan_case(row, stratum, cause_size=size, overlap=overlap,
                                     n=args.n, variant=local_variant,
                                     distractors=donors, style=args.style,
                                     all_active=args.all_active)
                handle.write(json.dumps(case.to_json(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

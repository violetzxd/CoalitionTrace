from __future__ import annotations

import argparse
import json
from pathlib import Path

from coalitiontrace.benchmark_holdout import make_holdout_case


def _documents(row: dict) -> list[str]:
    return [str(doc.get("text", "")) for doc in row.get("documents", [])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=70)
    parser.add_argument("--split")
    parser.add_argument("--n", type=int, default=8)
    args = parser.parse_args()
    normalized = []
    with args.input.open(encoding="utf-8") as source:
        source_rows = (json.loads(line) for line in source if line.strip())
        for row in source_rows:
            if args.split and row.get("split") != args.split:
                continue
            item = dict(row)
            if "correct" not in item:
                answers = item.get("answers") or []
                if not answers:
                    continue
                item["correct"] = str(answers[0])
            normalized.append(item)
            if len(normalized) >= args.limit:
                break
    if not normalized:
        raise ValueError("no eligible source rows")
    configs = [
        ("U", 2, 0),
        ("A", 2, 0), ("A", 2, 1),
        ("N", 2, 0), ("N", 2, 1),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(normalized):
            donors: list[str] = []
            for offset in range(1, len(normalized)):
                donors.extend(_documents(normalized[(index + offset) % len(normalized)]))
                if len(donors) >= 2 * args.n:
                    break
            for stratum, size, variant in configs:
                case = make_holdout_case(
                    row, stratum, cause_size=size, variant=variant,
                    n=args.n, distractors=donors,
                )
                handle.write(json.dumps(case.to_json(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

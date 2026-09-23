from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random

from coalitiontrace.benchmark import _pad_like
from coalitiontrace.core import CoalitionCase


def permute(case: CoalitionCase) -> CoalitionCase:
    order = list(range(case.n))
    seed = int(hashlib.sha256(f"{case.case_id}:order-audit".encode()).hexdigest()[:16], 16)
    random.Random(seed).shuffle(order)
    if order == list(range(case.n)):
        order = order[1:] + order[:1]
    inverse = {old: new for new, old in enumerate(order)}
    return replace(
        case,
        case_id=f"{case.case_id}:order2",
        family=f"{case.family}:order2",
        observed=tuple(case.observed[i] for i in order),
        replacements=tuple(case.replacements[i] for i in order),
        poison_indices=tuple(sorted(inverse[i] for i in case.poison_indices)),
        planted_causes=tuple(
            tuple(sorted(inverse[i] for i in cause)) for cause in case.planted_causes
        ),
        template_id=f"{case.template_id}-order2",
    )


def replace_neutral(case: CoalitionCase) -> CoalitionCase:
    replacements = []
    for i, (observed, replacement) in enumerate(zip(case.observed, case.replacements)):
        if observed == replacement:
            replacements.append(replacement)
            continue
        neutral = (
            f"Alternative neutral control {i}: a routine library circulation note "
            "with no entity answer, routing identifier, revocation, or audit result."
        )
        replacements.append(_pad_like(neutral, replacement))
    return replace(
        case,
        case_id=f"{case.case_id}:replacement2",
        family=f"{case.family}:replacement2",
        replacements=tuple(replacements),
        template_id=f"{case.template_id}-replacement2",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--stratum", default="N")
    parser.add_argument("--mode", choices=["order", "replacement"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selected = {
        row["case_id"] for row in map(json.loads, args.selection.open(encoding="utf-8"))
        if row["stratum"] == args.stratum
    }
    transform = permute if args.mode == "order" else replace_neutral
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8") as handle:
        for row in map(json.loads, args.cases.open(encoding="utf-8")):
            case = CoalitionCase.from_json(row)
            if case.case_id not in selected:
                continue
            handle.write(json.dumps(transform(case).to_json(), ensure_ascii=False) + "\n")
            count += 1
    print(json.dumps({"mode": args.mode, "stratum": args.stratum, "cases": count}))


if __name__ == "__main__":
    main()

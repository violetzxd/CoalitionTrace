from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from coalitiontrace.benchmark_confirmatory2 import make_confirmatory2_case


def _clean(value: str) -> str:
    return " ".join(str(value).replace("\n", " ").split()).strip()


def _squad(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for article in raw["data"]:
        for paragraph in article["paragraphs"]:
            for qa in paragraph["qas"]:
                answers = qa.get("answers") or []
                if answers:
                    rows.append({
                        "id": f"squad:{qa['id']}",
                        "question": _clean(qa["question"]),
                        "correct": _clean(answers[0]["text"]),
                    })
    return rows


def _webquestions(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [{
        "id": f"webquestions:{row['qId']}",
        "question": _clean(row["qText"]),
        "correct": _clean(row["answers"][0]),
    } for row in raw if row.get("answers")]


def _rank(row: dict) -> str:
    return hashlib.sha256(("confirmatory2-source|" + row["id"]).encode()).hexdigest()


def _norm_question(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _eligible(rows: list[dict], excluded: set[str]) -> list[dict]:
    rows = [r for r in rows if r["question"] and 0 < len(r["correct"]) <= 60
            and _norm_question(r["question"]) not in excluded]
    rows.sort(key=_rank)
    unique = []
    seen = set()
    for row in rows:
        normalized = _norm_question(row["question"])
        if normalized not in seen:
            unique.append(row)
            seen.add(normalized)
    if len(unique) < 440:
        raise ValueError("fewer than 220 sources plus 220 disjoint target donors")
    sources, donors = unique[:220], unique[220:440]
    for index, row in enumerate(sources):
        for offset in range(len(donors)):
            candidate = donors[(index + offset) % len(donors)]["correct"]
            if candidate.casefold() != row["correct"].casefold():
                row["target"] = candidate
                break
    return sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=("squad", "webquestions"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partition", choices=("pilot", "final"), required=True)
    parser.add_argument("--exclude-questions", type=Path)
    args = parser.parse_args()
    excluded = set()
    if args.exclude_questions:
        excluded = {line.strip() for line in args.exclude_questions.read_text(
            encoding="utf-8").splitlines() if line.strip()}
    rows = _eligible(_squad(args.input) if args.dataset == "squad"
                     else _webquestions(args.input), excluded)
    selected = rows[:40] if args.partition == "pilot" else rows[40:220]
    configs = [("U", 0), ("A", 0), ("N", 0), ("N", 1)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in selected:
            for stratum, variant in configs:
                case = make_confirmatory2_case(row, stratum, variant=variant)
                handle.write(json.dumps(case.to_json(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

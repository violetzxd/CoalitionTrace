#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from coalitiontrace.core import CoalitionCase, build_prompt


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _question_digest(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


def _contains_phrase(text: str, phrase: str) -> bool:
    haystack = _norm(text).split()
    needle = _norm(phrase).split()
    return bool(needle) and any(
        haystack[index:index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, action="append", required=True)
    parser.add_argument("--prior-questions", type=Path, required=True)
    parser.add_argument("--assets-lock", type=Path)
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prior = set(args.prior_questions.read_text(encoding="utf-8").splitlines())
    seen_case_ids, file_sources, file_questions = set(), {}, {}
    generic_collisions = 0
    neutral_leaks = []
    role_positions: dict[str, Counter] = defaultdict(Counter)
    cases_by_file = {}
    for path in args.case:
        cases = [CoalitionCase.from_json(json.loads(line)) for line in
                 path.read_text(encoding="utf-8").splitlines() if line]
        cases_by_file[path.name] = cases
        sources = {case.source_id for case in cases}
        questions = {_question_digest(case.question) for case in cases}
        file_sources[path.name] = sources
        file_questions[path.name] = questions
        if questions & prior:
            raise ValueError(f"prior-question overlap in {path}")
        for case in cases:
            if case.case_id in seen_case_ids:
                raise ValueError(f"duplicate case id: {case.case_id}")
            seen_case_ids.add(case.case_id)
            requests = ["\n".join(build_prompt(case, mask))
                        for mask in range(1 << case.n)]
            generic_collisions += len(requests) - len(set(requests))
            for index, replacement in enumerate(case.replacements):
                if (_contains_phrase(replacement, case.target)
                        or _contains_phrase(replacement, case.correct)):
                    neutral_leaks.append([case.case_id, index])
            if case.planted_stratum == "N":
                for index, text in enumerate(case.observed):
                    lower = text.casefold().lstrip()
                    if (lower.startswith("scope bulletin for")
                            or lower.startswith("disambiguation index for")):
                        role_positions["shift"][index] += 1
                    if (lower.startswith("jurisdiction ruling")
                            or lower.startswith("evaluation scope addendum")):
                        role_positions["restore"][index] += 1

    names = list(cases_by_file)
    overlaps = {}
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            overlaps[f"{left}|{right}"] = {
                "source_ids": len(file_sources[left] & file_sources[right]),
                "normalized_questions": len(file_questions[left] & file_questions[right]),
            }
    if any(v["source_ids"] or v["normalized_questions"] for v in overlaps.values()):
        raise ValueError("pilot/final or cross-dataset source overlap")
    if generic_collisions or neutral_leaks:
        raise ValueError(
            f"request collisions={generic_collisions}; neutral leaks="
            f"{len(neutral_leaks)} examples={neutral_leaks[:5]}"
        )

    chat_collisions = {}
    if args.assets_lock:
        from transformers import AutoTokenizer
        lock = json.loads(args.assets_lock.read_text(encoding="utf-8"))["models"]
        for model_name in args.model:
            tokenizer = AutoTokenizer.from_pretrained(
                lock[model_name]["path"], local_files_only=True
            )
            collisions = 0
            for cases in cases_by_file.values():
                for case in cases:
                    rendered = []
                    for mask in range(1 << case.n):
                        system, user = build_prompt(case, mask)
                        prompt = tokenizer.apply_chat_template([
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ], tokenize=False, add_generation_prompt=True)
                        rendered.append(hashlib.sha256(prompt.encode()).hexdigest())
                    collisions += len(rendered) - len(set(rendered))
            chat_collisions[model_name] = collisions
            if collisions:
                raise ValueError(f"chat-template collisions for {model_name}")

    output = {
        "status": "PASS",
        "files": {name: len(cases) for name, cases in cases_by_file.items()},
        "case_ids": len(seen_case_ids),
        "generic_request_collisions": generic_collisions,
        "chat_template_collisions": chat_collisions,
        "neutral_replacement_leaks": len(neutral_leaks),
        "pairwise_overlaps": overlaps,
        "n_role_position_counts": {
            role: [counts[index] for index in range(8)]
            for role, counts in role_positions.items()
        },
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()

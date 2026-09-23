#!/usr/bin/env python3
"""Build a normalized-question exclusion list from prior case JSONL files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--input", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    questions = set()
    paths = list(args.input)
    if args.input_dir:
        paths.extend(sorted(args.input_dir.glob("*.jsonl")))
    paths = sorted(set(paths))
    if not paths:
        raise ValueError("at least one --input or --input-dir is required")
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                question = row.get("question")
                if question:
                    questions.add(_normalize(str(question)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sorted(questions)) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(paths),
                      "normalized_questions": len(questions)}))


if __name__ == "__main__":
    main()

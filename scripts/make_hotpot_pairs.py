from __future__ import annotations

import argparse
import json
from pathlib import Path

from coalitiontrace.benchmark import make_pair_case, read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--families", nargs="+", default=["bridge", "trigger_payload"])
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("w", encoding="utf-8") as out:
        for row in read_jsonl(args.input):
            if not row.get("question") or not str(row.get("target", "")).strip():
                continue
            for family in args.families:
                out.write(json.dumps(make_pair_case(row, family).to_json(), ensure_ascii=False) + "\n")
                written += 1
            if written >= args.limit * len(args.families):
                break
    print(json.dumps({"cases": written, "output": str(args.output)}))


if __name__ == "__main__":
    main()


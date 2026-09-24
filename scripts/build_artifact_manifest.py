#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__"}
EXCLUDED_SUFFIXES = {
    ".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".out",
    ".pyc", ".synctex.gz",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    rows = []
    for path in sorted(p for p in args.root.rglob("*")
                       if p.is_file()
                       and not EXCLUDED_PARTS.intersection(p.parts)
                       and not any(p.name.endswith(suffix)
                                   for suffix in EXCLUDED_SUFFIXES)):
        if path.resolve() == output:
            continue
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        rows.append(f"{digest}  {path.relative_to(args.root).as_posix()}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"manifested {len(rows)} files")


if __name__ == "__main__":
    main()

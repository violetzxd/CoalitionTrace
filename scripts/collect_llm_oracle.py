from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from coalitiontrace.core import (
    CoalitionCase, build_prompt, extract_short_answer, normalized_exact_match,
)


def load_cases(path: Path, limit: int | None) -> list[CoalitionCase]:
    rows = [CoalitionCase.from_json(json.loads(line)) for line in path.open(encoding="utf-8")]
    return rows if limit is None else rows[:limit]


def masks(case: CoalitionCase, mode: str) -> list[int]:
    if mode == "all":
        return list(range(1 << case.n))
    poison = case.poison_mask
    base = ((1 << case.n) - 1) & ~poison
    return [base | sub for sub in (0, 1 << case.poison_indices[0], 1 << case.poison_indices[1], poison)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-lock", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case-ids", type=Path)
    parser.add_argument("--mask-mode", choices=["poison4", "all"], default="poison4")
    parser.add_argument("--max-new-tokens", type=int, default=16)
    args = parser.parse_args()

    lock = json.loads(args.assets_lock.read_text())["models"][args.model]
    tokenizer = AutoTokenizer.from_pretrained(lock["path"], local_files_only=True, padding_side="left")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        lock["path"], local_files_only=True, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to(args.device).eval()
    cases = load_cases(args.cases, args.limit)
    if args.case_ids:
        selected = {line.strip() for line in args.case_ids.open(encoding="utf-8") if line.strip()}
        cases = [case for case in cases if case.case_id in selected]
    done = set()
    if args.output.exists():
        for line in args.output.open(encoding="utf-8"):
            row = json.loads(line); done.add((row["case_id"], int(row["mask"])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw_pending = [(case, mask) for case in cases for mask in masks(case, args.mask_mode)
                   if (case.case_id, mask) not in done]
    # Deterministic decoding makes byte-identical rendered prompts exact duplicate
    # interventions. Group them for oracle construction, while emitting every mask
    # so the complete Boolean lattice remains explicit and independently auditable.
    grouped = {}
    for case, mask in raw_pending:
        system, user = build_prompt(case, mask)
        prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True,
        )
        key = hashlib.sha256(prompt.encode()).hexdigest()
        grouped.setdefault(key, {"prompt": prompt, "aliases": []})["aliases"].append((case, mask))
    pending = list(grouped.values())
    started = time.time()
    with args.output.open("a", encoding="utf-8") as out:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start + args.batch_size]
            prompts = [job["prompt"] for job in batch]
            encoded = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True, max_length=4096).to(args.device)
            before = encoded.input_ids.shape[1]
            with torch.inference_mode():
                generated = model.generate(
                    **encoded, do_sample=False, max_new_tokens=args.max_new_tokens,
                    pad_token_id=tokenizer.eos_token_id, use_cache=True,
                    temperature=None, top_p=None, top_k=None,
                )
            answers = tokenizer.batch_decode(generated[:, before:], skip_special_tokens=True)
            for batch_index, (job, answer) in enumerate(zip(batch, answers)):
                answer = answer.strip()
                extracted = extract_short_answer(answer)
                for case, mask in job["aliases"]:
                    row = {
                        "case_id": case.case_id, "family": case.family, "n": case.n,
                        "mask": mask, "answer": answer, "extracted_answer": extracted,
                        "utility": normalized_exact_match(extracted, case.target),
                        "correct_em": normalized_exact_match(extracted, case.correct),
                        "target": case.target, "correct": case.correct,
                        "model": args.model, "revision": lock["revision"],
                        "prompt_sha256": hashlib.sha256(prompts[batch_index].encode()).hexdigest(),
                        "replay_group_size": len(job["aliases"]),
                        "decoding": {"do_sample": False, "max_new_tokens": args.max_new_tokens},
                        "input_tokens": int(encoded.attention_mask[batch_index].sum()),
                        "output_tokens": int((generated[batch_index, before:] != tokenizer.pad_token_id).sum()),
                    }
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
            print(json.dumps({"completed": min(start + len(batch), len(pending)), "total": len(pending), "seconds": round(time.time()-started, 1)}), flush=True)


if __name__ == "__main__":
    main()

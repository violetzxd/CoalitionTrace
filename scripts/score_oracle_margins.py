from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from coalitiontrace.core import CoalitionCase, build_prompt


def conditional_mean_logprobs(model, tokenizer, items, device, batch_size):
    values = []
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        sequences, answer_lengths = [], []
        for prompt, answer in batch:
            prompt_ids = tokenizer(prompt, add_special_tokens=False).input_ids
            answer_ids = tokenizer(answer, add_special_tokens=False).input_ids
            if not answer_ids:
                answer_ids = [tokenizer.eos_token_id]
            sequences.append(prompt_ids + answer_ids)
            answer_lengths.append(len(answer_ids))
        encoded = tokenizer.pad({"input_ids": sequences}, padding=True, return_tensors="pt").to(device)
        with torch.inference_mode():
            logits = model(**encoded).logits[:, :-1].float()
            log_probs = torch.log_softmax(logits, dim=-1)
        for row_index, answer_length in enumerate(answer_lengths):
            valid_length = int(encoded.attention_mask[row_index].sum())
            pad_length = encoded.input_ids.shape[1] - valid_length
            answer_start = encoded.input_ids.shape[1] - answer_length
            positions = torch.arange(answer_start - 1, encoded.input_ids.shape[1] - 1,
                                     device=device)
            tokens = encoded.input_ids[row_index, answer_start:]
            token_logps = log_probs[row_index, positions, tokens]
            values.append(float(token_logps.mean().cpu()))
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-lock", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--stratum", default="N")
    parser.add_argument("--violation-edges-only", action="store_true")
    args = parser.parse_args()
    cases = {case.case_id: case for case in (
        CoalitionCase.from_json(json.loads(line)) for line in args.cases.open(encoding="utf-8")
    )}
    rows = [json.loads(line) for line in args.oracle.open(encoding="utf-8")]
    if args.selection:
        selected = {
            row["case_id"] for row in map(json.loads, args.selection.open(encoding="utf-8"))
            if row["stratum"] == args.stratum
        }
        rows = [row for row in rows if row["case_id"] in selected]
    if args.violation_edges_only:
        by_case = defaultdict(dict)
        for row in rows:
            by_case[row["case_id"]][int(row["mask"])] = float(row["utility"])
        relevant = set()
        for case_id, values in by_case.items():
            n = cases[case_id].n
            full = (1 << n) - 1
            for lower, value in values.items():
                if value < 1.0:
                    continue
                remaining = full & ~lower
                while remaining:
                    bit = remaining & -remaining
                    upper = lower | bit
                    if values[upper] < 1.0:
                        relevant.add((case_id, lower))
                        relevant.add((case_id, upper))
                    remaining -= bit
        rows = [row for row in rows if (row["case_id"], int(row["mask"])) in relevant]
    lock = json.loads(args.assets_lock.read_text())["models"][args.model]
    tokenizer = AutoTokenizer.from_pretrained(lock["path"], local_files_only=True,
                                               padding_side="left")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        lock["path"], local_files_only=True, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to(args.device).eval()
    # Exact prompt-equivalent masks share both generation and teacher-forced
    # scores. Preserve all member masks in the output for edge reconstruction.
    groups = defaultdict(list)
    for row in rows:
        groups[(row["case_id"], row.get("prompt_sha256", str(row["mask"])))].append(row)
    unique_rows = []
    for members in groups.values():
        representative = dict(members[0])
        representative["equivalent_masks"] = sorted(int(row["mask"]) for row in members)
        unique_rows.append(representative)
    items = []
    for row in unique_rows:
        case = cases[row["case_id"]]
        system, user = build_prompt(case, int(row["mask"]))
        prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True,
        )
        items.extend([(prompt, case.target), (prompt, case.correct)])
    scores = conditional_mean_logprobs(model, tokenizer, items, args.device, args.batch_size)
    for index, row in enumerate(unique_rows):
        target_lp, correct_lp = scores[2 * index:2 * index + 2]
        margin = target_lp - correct_lp
        row.update({
            "target_mean_logprob": target_lp,
            "correct_mean_logprob": correct_lp,
            "target_correct_margin": margin,
            "target_preference": 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, margin)))),
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in unique_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

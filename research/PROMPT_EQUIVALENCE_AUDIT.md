# Prompt-equivalence audit protocol

Frozen after the independent round-1 review and before the all-active control.
This is a corrective audit prompted by a discovered accounting defect; it is not
part of the original confirmatory hypothesis.

## Query domain

For document mask `S`, let `render(S)` be the exact system-plus-user prompt byte
sequence passed to the tokenizer. Define `S ~ T` iff `render(S)=render(T)` and
let `Q=2^D/~`. A deterministic generator needs one replay per queried equivalence
class, not one replay per syntactic mask.

Every method receives an identical cache keyed by SHA-256 of the rendered prompt.
The primary corrected budget counts unique prompt hashes. We additionally retain:

- unique syntactic masks touched;
- unique prompt hashes replayed;
- total input and output tokens;
- wall time;
- the full-domain ratio `|Q|/2^n`;
- descriptive effective query dimension `log2|Q|`.

The last quantity is only a description of finite domain size; it is not called a
statistical or intrinsic dimension.

## Retrospective comparison

On exactly the same selected registry cases and unchanged method settings, report
the frozen mask-budget result beside the corrected prompt-budget result. A change
in ranking or apparent efficiency is an audit finding, not a new superiority
test. Source queries remain the sampling unit.

## All-active control

The registry benchmark deliberately kept noncausal slots unchanged across the
observed and replacement contexts. The all-active control instead gives every
slot distinct observed and replacement text. Noncausal replacements are matched
neutral passages that omit the target, correct answer and routing identifiers.
The control is accepted only when all `2^n` rendered prompt hashes are distinct.

For each dataset--generator pair, screen an independent extension cohort and
retain at least 30 oracle-A cases at `n=8`. Report the all-active cell separately;
never pool it with the collapsed registry domain. The audit is falsified as a
headline contribution if correct caching does not materially alter cost or method
ranking in all four primary cells, or if the all-active control shows that the
effect is solely the avoidable fixed-slot construction.

## Natural duplicate-context check

On unmodified retrieved contexts, record exact duplicate chunks, empty/padding
chunks and duplicate rendered prompts under masking. Near-duplicates are not
deduplicated in the primary audit. Any extension to semantic caching requires a
separate error analysis and is out of scope for this paper.

# Protocol deviations and post-hoc analyses

This register is intentionally explicit: no post-hoc analysis below is relabeled
as confirmatory.

## Sample-size feasibility deviation

The early pivot protocol requested at least 100 test source queries per
dataset--model--stratum. The pinned public PoisonedRAG asset contains only 100
queries per dataset, of which 30 were frozen as development and 70 as test.
Method-blind screening of the 70 test sources yielded 45--60 cases per stratum,
depending on dataset and generator. We therefore report every cell separately
and use the later independent-review floor of 40 sources per cell; we do not claim
to have met the literal 100-per-cell target. No template variant is counted as an
independent source.

## Prompt-equivalence accounting correction

After the first two Qwen confirmatory cells, independent review found that the
method cache and budget were keyed by syntactic masks although the deterministic
oracle collector reused byte-identical rendered prompts. This made the reported
generator-call cost inconsistent. The implementation was corrected before the
Mistral method results were read, and every dataset--model cell is re-evaluated
from unchanged oracle tables with a shared prompt-hash cache.

The corrected analysis is a post-hoc audit. The originally frozen mask-budget
primary comparison remains reported as such, but its generator-cost
interpretation is withdrawn. No threshold, selected case or oracle label changed.

## Added standard enumerator

The original baseline set omitted the closest monotone minimal-explanation
enumerator. After review, a standard exclusion/hitting-set enumerator using the
same balanced minimizer and cache was added. It is a mandatory strong baseline,
not a confirmatory method introduced to improve results. Matching or superior
performance terminates algorithmic novelty claims.

## N upward audit

The upward-edge audit was designed after observing failed N detection on the
first held-out NQ/Qwen cell. It is exploratory. It never replaces the frozen
AmbiCause result and is not pooled into confirmatory estimates.

## Enumerate-first residual audit

The residual audit was designed after observing the frozen method's low N
sensitivity and is therefore post-hoc. It preserves the standard enumerator's
entire query prefix, then uses only remaining prompt-hash budget. The final
prompt-uniform randomized schedule was chosen after comparing deterministic
upward, downward, bidirectional, shuffled-boundary, and random schedules. All
registry estimates and the budget curve are exploratory. The already frozen
news wording is used as a transfer cohort, not relabeled as an untouched
confirmatory test; the all-active cohort is retained as a negative stress test.

Final review found that an observed prompt-equivalence class must be closed over
all of its masks before lattice witness checks. The implementation and every
residual-audit result were recomputed with this zero-call closure. It also found
that pooled bootstrap units must be dataset/source clusters spanning both model
outcomes; all reported pooled intervals and paired gains were recomputed on that
unit. Neither correction is treated as a new confirmatory analysis.

## Additional robustness cohorts

The `news` wording family was frozen before confirmatory outputs and is a planned
descriptive robustness analysis. The all-active control, prompt-margin audit,
standard-enumerator comparison and `n=10` subset were added after independent
review and are post-hoc validation. They are labeled accordingly in artifacts and
the manuscript.

Of the four `n=10` A cells, only Qwen/Hotpot reaches the later 40-source floor
(`n=40`); Qwen/NQ and Mistral Hotpot/NQ contain 27, 34 and 32 sources and are
descriptive. The all-active construction yields very few A sources and shifts
many planted-A candidates to realized N; it is treated as a construction-validity
stress test rather than a powered method comparison.

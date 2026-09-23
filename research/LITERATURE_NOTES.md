# Literature map for the pivot

Search frozen on 2026-09-20.  These notes are claim-level pointers; the manuscript
must verify bibliographic metadata against the linked primary sources.

## Closest technical antecedents

- Carter et al., **Understanding Black-box Decisions with Sufficient Input
  Subsets**, AISTATS 2019. Defines standalone sufficient input subsets and directly
  precedes our minimal-sufficiency language. The paper must cite this and avoid
  claiming that minimal sufficient subsets are new.
  <https://proceedings.mlr.press/v89/carter19a.html>
- Marques-Silva et al., **Explanations for Monotonic Classifiers**, ICML 2021.
  Formal abductive/contrastive explanations, black-box monotone classifiers and
  explanation enumeration; establishes the hitting-set/minimal-explanation
  neighborhood of our exclusion tree.
  <https://proceedings.mlr.press/v139/marques-silva21a.html>
- Cohen-Wang et al., **ContextCite: Attributing Model Generation to Context**,
  arXiv 2024. Scalable context attribution via a mask-based surrogate, including a
  poisoning application; primary RAG attribution baseline.
  <https://arxiv.org/abs/2409.00729>
- Chuang et al., **SelfCite: Self-Supervised Alignment for Context Attribution in
  Large Language Models**, ICML 2025. Uses necessity/sufficiency under context
  ablation as a citation reward. This is especially close conceptually but targets
  generated citations rather than enumerating all local document causes.
  <https://proceedings.mlr.press/v267/chuang25a.html>
- Qi et al., **Model Internals-based Answer Attribution for Trustworthy RAG
  (MIRAGE)**, EMNLP 2024. Internal saliency-based token/document attribution and a
  necessary comparison point for faithfulness claims.
  <https://aclanthology.org/2024.emnlp-main.347/>

## Risk, interference, and poisoning context

- Chen et al., **Controlling Risk of RAG: A Counterfactual Prompting Framework**,
  Findings of EMNLP 2024. Motivates selective risk and abstention.
  <https://aclanthology.org/2024.findings-emnlp.133/>
- Shi et al., **Large Language Models Can Be Easily Distracted by Irrelevant
  Context**, ICML 2023. Supports treating non-monotonicity/distractor interference
  as a real behavior rather than merely an algorithmic corner case.
  <https://proceedings.mlr.press/v202/shi23a.html>
- Chen et al., **TRACE: Tracing Target Answers in Poisoned Retrieval Corpora via
  Token Influence Attribution**, arXiv 2026. A current poisoning-localization
  competitor; compare task definitions carefully because TRACE finds influential
  tokens, not all inclusion-minimal document causes.
  <https://arxiv.org/abs/2606.25721>

## Defensible novelty boundary

The paper must not claim novelty for sufficient subsets, monotone explanation
enumeration, or hitting-set branching.  The potentially new contribution is the
combination of: (i) a set-valued local RAG cause target, (ii) the exact LOO
backbone boundary, (iii) a fully oracled U/A/N benchmark exposing alternative
causes and unsafe completeness, and (iv) budget/abstention evaluation for RAG.

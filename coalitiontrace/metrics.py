from __future__ import annotations


def member_f1(predicted: int | None, truth: int) -> float:
    if predicted is None:
        return 0.0
    tp = (predicted & truth).bit_count()
    precision = tp / max(1, predicted.bit_count())
    recall = tp / max(1, truth.bit_count())
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def member_f1_any(predicted: int | None, truths: tuple[int, ...]) -> float:
    """Best F1 against the complete set of equally valid oracle minima."""
    if not truths:
        return float(predicted is None)
    return max(member_f1(predicted, truth) for truth in truths)


def exact_any(predicted: int | None, minima: tuple[int, ...]) -> int:
    return int(predicted is not None and predicted in minima)

"""Pure functions for inter-prompt agreement. No I/O, so they are tested on literal lists."""
from collections import Counter


def cohen_kappa(first, second):
    """Cohen's kappa for two equal-length label lists. Returns None when it is undefined
    (no items, or both raters used a single identical category so chance agreement is 1)."""
    if len(first) != len(second):
        raise ValueError("label lists differ in length")
    total = len(first)
    if total == 0:
        return None
    observed = sum(a == b for a, b in zip(first, second)) / total
    first_counts, second_counts = Counter(first), Counter(second)
    expected = sum(first_counts[value] * second_counts[value] for value in first_counts) / (total * total)
    if expected == 1.0:
        return None
    return (observed - expected) / (1 - expected)


def mean_jaccard(first_sets, second_sets):
    """Mean Jaccard overlap for multi-label answers; None when there are no items."""
    if len(first_sets) != len(second_sets):
        raise ValueError("label lists differ in length")
    if not first_sets:
        return None
    scores = []
    for a, b in zip(first_sets, second_sets):
        a, b = set(a), set(b)
        scores.append(len(a & b) / len(a | b) if (a | b) else 1.0)
    return sum(scores) / len(scores)

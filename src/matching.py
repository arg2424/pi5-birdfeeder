"""Matching cosinus entre embeddings d'individus."""
from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a <= 1e-12 or norm_b <= 1e-12:
        return 0.0
    return dot / (norm_a * norm_b)


class IndividualMatcher:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def match(
        self,
        embedding: list[float],
        candidates: list[tuple[int, list[float]]],
    ) -> tuple[int, float] | None:
        best_id = None
        best_score = -1.0
        for individual_id, prototype in candidates:
            score = cosine_similarity(embedding, prototype)
            if score > best_score:
                best_id = individual_id
                best_score = score
        if best_id is None or best_score < self.threshold:
            return None
        return best_id, best_score

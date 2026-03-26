from src.matching import cosine_similarity, IndividualMatcher


def test_cosine_similarity_identity():
    a = [1.0, 2.0, 3.0]
    assert abs(cosine_similarity(a, a) - 1.0) < 1e-9


def test_matcher_returns_best_candidate():
    matcher = IndividualMatcher(threshold=0.7)
    emb = [1.0, 0.0, 0.0]
    candidates = [
        (1, [0.9, 0.1, 0.0]),
        (2, [0.1, 0.9, 0.0]),
    ]
    match = matcher.match(emb, candidates)
    assert match is not None
    individual_id, _ = match
    assert individual_id == 1

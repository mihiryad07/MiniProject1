from src.evaluation import (
    average_precision,
    mean_average_precision,
    precision_at_k,
    recall_at_k,
)


def test_precision_recall_and_average_precision():
    relevant = ["shirt-jeans-shoes", "dress-shoes"]
    ranking = ["shirt-jeans-shoes", "two-shirts", "dress-shoes"]

    assert precision_at_k(relevant, ranking, 2) == 0.5
    assert recall_at_k(relevant, ranking, 2) == 0.5

    ap = average_precision(relevant, ranking)
    assert ap == ((1.0 + (2.0 / 3.0)) / 2.0)


def test_mean_average_precision_across_queries():
    relevant = {
        "q1": ["a", "b"],
        "q2": ["c"],
    }
    rankings = {
        "q1": ["a", "x", "b"],
        "q2": ["x", "c"],
    }

    q1_ap = (1.0 + (2.0 / 3.0)) / 2.0
    q2_ap = 0.5
    assert mean_average_precision(relevant, rankings) == (q1_ap + q2_ap) / 2.0

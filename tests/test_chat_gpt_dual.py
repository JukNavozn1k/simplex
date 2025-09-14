import pytest
from simplex.dual import dual_simplex

@pytest.mark.parametrize("c,A,b", [
    # infeasible: x <= 1 и одновременно x >= 2 (противоречие)
    ([1], [[1], [-1]], [1, -2]),

    # infeasible: x1 + x2 <= 1 и одновременно x1 + x2 >= 5
    ([1, 1], [[1, 1], [-1, -1]], [1, -5]),

    # infeasible: x >= 0, но правая часть отрицательная
    ([1, 1], [[1, 0], [0, 1]], [-1, -2]),
])
def test_infeasible_cases(c, A, b):
    res = dual_simplex(c, A, b)
    assert res.status == "infeasible"


@pytest.mark.parametrize("c,A,b", [
    # unbounded: maximize x1, только ограничение x1 >= 1
    ([1], [[-1]], [-1]),

    # unbounded: maximize x2, ограничение x1 >= 0 (x2 свободен и может расти)
    ([0, 1], [[-1, 0]], [0]),

    # unbounded: maximize 2x1 + 3x2 при условии x1 - x2 >= 1
    ([2, 3], [[-1, 1]], [-1]),
])
def test_unbounded_cases(c, A, b):
    res = dual_simplex(c, A, b)
    assert res.status == "unbounded"


@pytest.mark.parametrize("c,A,b,expected_obj", [
    # alternative optima: цель 0, любое решение подходит
    ([0, 0], [[1, 0], [0, 1]], [3, 4], 0.0),

    # multiple optima: x1 + x2 = 2, максимум 2
    ([1, 1], [[1, 1], [2, 2]], [2, 4], 2.0),
])
def test_optimal_and_alternative_cases(c, A, b, expected_obj):
    res = dual_simplex(c, A, b)
    assert res.status == "optimal"
    assert pytest.approx(res.objective, rel=1e-6) == expected_obj

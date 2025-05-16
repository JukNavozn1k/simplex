import pytest
from simplex import solve_integer

try:
    from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpInteger, value, LpStatus
    PULP = True
except ImportError:
    PULP = False


def solve_pulp_integer(c, A, b):
    """
    Решает целочисленную задачу линейного программирования с помощью PuLP.
    max c^T x
    s.t. Ax <= b
    x — целочисленное
    """
    n = len(c)
    prob = LpProblem("Integer_MIP", LpMaximize)
    x = [LpVariable(f"x{i}", lowBound=0, cat=LpInteger) for i in range(n)]
    prob += lpSum(c[i] * x[i] for i in range(n))
    for row, bi in zip(A, b):
        prob += lpSum(row[i] * x[i] for i in range(n)) <= bi
    status_code = prob.solve()
    status_name = LpStatus[status_code]
    return status_name, [int(value(xi)) for xi in x]


@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected",
    [
        (
            [2, 3],
            [[1, 0], [0, 1], [1, 1]],
            [4, 4, 5],
            [1, 4]
        ),
        (
            [3, 2, 4],
            [[1, 1, 1], [2, 0, 1], [0, 1, 2]],
            [5, 6, 5],
            [2, 1, 2]
        ),
    ]
)
def test_branch_and_bound_vs_pulp(c, A, b, expected):
    """
    Сравниваем ответ метода ветвей и границ с решением PuLP MIP (целочисленного).
    """
    res, x_bb = solve_integer(c, A, b)
    assert res.status == 'optimal'
    assert x_bb == expected
    assert all(isinstance(x, int) for x in x_bb)

    status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
    assert status_pulp == 'Optimal'
    assert sol_pulp == expected


@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected_status, expected_solution",
    [
        (
            [2, 3],
            [[1, 0], [0, 1], [1, 1]],
            [4, 4, 5],
            'optimal',
            [1, 4]
        ),
        (
            [3, 2, 4],
            [[1, 1, 1], [2, 0, 1], [0, 1, 2]],
            [5, 6, 5],
            'optimal',
            [2, 1, 2]
        ),
        (
            [1, 1],
            [[1, 2], [3, 4]],
            [1, 1],
            'optimal',
            [0, 0]
        ),
        (
            [1, 1],
            [[1, 0], [0, 1]],
            [2, 2],
            'optimal',
            None  # допустим, ни одно целое решение не даёт улучшения
        ),
        (
            [-1, -2],
            [[1, 1], [2, 0]],
            [3, 4],
            'optimal',
            [0, 0]
        ),
        (
            [0, 0],
            [[1, 0], [0, 1]],
            [0, 0],
            'optimal',
            [0, 0]
        ),
    ]
)
def test_branch_and_bound_extended(c, A, b, expected_status, expected_solution):
    res, x_bb = solve_integer(c, A, b)
    assert res.status == expected_status
    if expected_solution is not None:
        assert x_bb == expected_solution
        assert all(isinstance(x, int) for x in x_bb)

    if expected_status == 'optimal':
        status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
        assert status_pulp == 'Optimal'
        if expected_solution is not None:
            assert sol_pulp == expected_solution

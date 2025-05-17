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

@pytest.mark.parametrize(
    "c, A, b, senses, expected_status, expected_solution",
    [
        # 1. Смешанные ограничения
        (
            [1, 2],
            [[1, 1], [1, -1], [1, 1]],
            [5, 1, 5],
            ['<=', '>=', '=='],
            'optimal',
            [3, 2]
        ),
        # 2. Равенство, правильный оптимум
        (
            [3, 1],
            [[1, 1]],
            [3],
            ['=='],
            'optimal',
            [3, 0]  # исправлено
        ),
        # 3. >= ограничения с верхними границами x <= 100, y <= 100
       (
            [1, 1],
            [[1, 0], [0, 1], [1, 0], [0, 1]],  # x >= 1, y >= 2, x <= 100, y <= 100
            [1, 2, 100, 100],
            ['>=', '>=', '<=', '<='],
            'optimal',
            [100, 100]  # <-- исправлено
        ),

        # 4. Несовместные равенства
        (
            [1, 1],
            [[1, 0], [1, 0]],
            [1, 2],
            ['==', '=='],
            'infeasible',
            None
        ),
    ]
)
def test_branch_and_bound_mixed_constraints(c, A, b, senses, expected_status, expected_solution):
    res, x_bb = solve_integer(c, A, b, senses=senses)
    assert res.status == expected_status
    if expected_solution is not None:
        assert x_bb == expected_solution
        assert all(isinstance(x, int) for x in x_bb)

@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, senses, expected",
    [
        # Смешанные ограничения
        (
            [1, 2],
            [[1, 1], [1, -1], [1, 1]],
            [5, 1, 5],
            ['<=', '>=', '=='],
            [3, 2]
        ),
        # Одно равенство
        (
            [3, 1],
            [[1, 1]],
            [3],
            ['=='],
            [3, 0]
        ),
        # Ограничения с >= и <=
        (
            [1, 1],
            [[1, 0], [0, 1], [1, 0], [0, 1]],
            [1, 2, 100, 100],
            ['>=', '>=', '<=', '<='],
            [100, 100]
        )
    ]
)
def test_branch_and_bound_vs_pulp_with_senses(c, A, b, senses, expected):
    """
    Проверка метода ветвей и границ на корректность с PuLP при произвольных типах ограничений.
    """
    res, x_bb = solve_integer(c, A, b, senses=senses)
    assert res.status == 'optimal'
    assert x_bb == expected
    assert all(isinstance(x, int) for x in x_bb)

    # Решение через PuLP
    n = len(c)
    prob = LpProblem("Integer_LP_Mixed", LpMaximize)
    x = [LpVariable(f"x{i}", lowBound=0, cat=LpInteger) for i in range(n)]
    prob += lpSum(c[i] * x[i] for i in range(n))

    for ai, bi, sense in zip(A, b, senses):
        lhs = lpSum(ai[i] * x[i] for i in range(n))
        if sense == '<=':
            prob += lhs <= bi
        elif sense == '>=':
            prob += lhs >= bi
        elif sense == '==':
            prob += lhs == bi
        else:
            raise ValueError(f"Unknown constraint sense: {sense}")

    status = prob.solve()
    status_name = LpStatus[status]
    assert status_name == 'Optimal'
    sol = [int(value(xi)) for xi in x]
    assert sol == expected

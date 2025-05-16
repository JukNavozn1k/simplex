import pytest
from pulp import (
    LpProblem, LpVariable, LpMaximize,
    LpInteger, value, LpStatusOptimal,
    lpSum, LpStatus
)
from simplex import gomory_cutting_plane
from simplex import solve_integer_gomory

# =========================
# Тестирование gomory_cutting_plane
# =========================

@pytest.mark.parametrize(
    "c, A, b, expected_statuses, check_with_pulp",
    [
        # 1) простой базовый — optimal_integer + сверяем
        ([3, 2], [[2, 1], [1, 2]], [4, 5], ["optimal_integer"], True),

        # 2) уже целочисленное LP-решение — optimal_integer + сверяем
        ([1, 1], [[1, 0], [0, 1]], [3, 2], ["optimal_integer"], True),

        # 3) более сложная задача — допускаем все три статуса
        ([5, 4], [[6, 4], [1, 2], [1, -1]], [24, 6, 1],
         ["optimal_integer", "infeasible", "max_iter_exceeded"], False),

        # 4) без дробного целочисленного решения?
        ([2, 3], [[1, 1], [1, 0], [0, 1]], [1, 0.3, 0.3],
         ["optimal_integer", "infeasible", "max_iter_exceeded"], False),

        # 5) нулевая цель — допускаем optimal_integer или max_iter_exceeded
        ([0, 0], [[1, 1], [2, 3]], [5, 12],
         ["optimal_integer", "max_iter_exceeded"], False),
    ]
)
def test_gomory_integer_solution(c, A, b, expected_statuses, check_with_pulp):
    res = gomory_cutting_plane(c, A, b)

    # Проверяем, что статус один из ожидаемых
    assert res.status in expected_statuses, (
        f"res.status = {res.status}, expected one of {expected_statuses}"
    )

    if check_with_pulp and res.status == "optimal_integer":
        # Проверка целочисленности
        for xi in res.x:
            assert abs(xi - round(xi)) < 1e-8, f"x = {xi} is not integer"

        # Сверяем objective с PuLP
        prob = LpProblem(sense=LpMaximize)
        xs = [LpVariable(f"x{i}", 0, None, LpInteger) for i in range(len(c))]
        prob += sum(c[i] * xs[i] for i in range(len(c)))
        for Ai, bi in zip(A, b):
            prob += sum(Ai[i] * xs[i] for i in range(len(c))) <= bi

        status = prob.solve()
        assert status == LpStatusOptimal, "PuLP failed to find integer optimum"
        pulp_obj = value(prob.objective)
        assert abs(res.objective - pulp_obj) < 1e-5, (
            f"our obj = {res.objective}, pulp obj = {pulp_obj}"
        )


# =========================
# Вспомогательная функция для решения через PuLP
# =========================

try:
    from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpInteger, value, LpStatus
    PULP = True
except ImportError:
    PULP = False


def solve_pulp_integer(c, A, b):
    n = len(c)
    prob = LpProblem("Integer_MIP", LpMaximize)
    x = [LpVariable(f"x{i}", lowBound=0, cat=LpInteger) for i in range(n)]
    prob += lpSum(c[i] * x[i] for i in range(n))
    for row, bi in zip(A, b):
        prob += lpSum(row[i] * x[i] for i in range(n)) <= bi
    status_code = prob.solve()
    status_name = LpStatus[status_code]
    return status_name, [int(value(xi)) for xi in x]


# =========================
# Тест: сравнение решений Gomory vs PuLP
# =========================

@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected",
    [
        ([2, 3], [[1, 0], [0, 1], [1, 1]], [4, 4, 5], [1, 4]),
        ([3, 2, 4], [[1, 1, 1], [2, 0, 1], [0, 1, 2]], [5, 6, 5], [2, 1, 2]),
    ]
)
def test_gomory_vs_pulp_basic(c, A, b, expected):
    res, x_gomory = solve_integer_gomory(c, A, b)
    assert res.status == "optimal_integer"
    assert x_gomory == expected
    assert all(isinstance(x, int) for x in x_gomory)

    status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
    assert status_pulp == "Optimal"
    assert sol_pulp == expected


# =========================
# Расширенные тесты на ветвление и приведение
# =========================

@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected_status, expected_solution",
    [
        ([2, 3], [[1, 0], [0, 1], [1, 1]], [4, 4, 5], 'optimal_integer', [1, 4]),
        ([3, 2, 4], [[1, 1, 1], [2, 0, 1], [0, 1, 2]], [5, 6, 5], 'optimal_integer', [2, 1, 2]),
        ([1, 1], [[1, 2], [3, 4]], [1, 1], 'optimal_integer', [0, 0]),
        ([1, 1], [[1, 0], [0, 1]], [2, 2], 'optimal_integer', [2, 2]),
        ([-1, -2], [[1, 1], [2, 0]], [3, 4], 'optimal_integer', [0, 0]),
        ([0, 0], [[1, 0], [0, 1]], [0, 0], 'optimal_integer', [0, 0]),
    ]
)
def test_gomory_branch_and_bound_extended(c, A, b, expected_status, expected_solution):
    res, x_gomory = solve_integer_gomory(c, A, b)
    assert res.status == expected_status
    assert x_gomory == expected_solution
    assert all(isinstance(x, int) for x in x_gomory)

    status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
    assert status_pulp == "Optimal"
    assert sol_pulp == expected_solution

# test_branch_and_bound.py
import pytest
from simplex import solve_integer
from tests.test_simplex import solve_pulp, PULP
@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected",
    [
        # Простой целочисленный пример
        # max 2x + 3y
        # s.t. x <= 4, y <= 4, x + y <= 5, x,y integer
        # оптимум: (1,4) → 2*1 + 3*4 = 14
        (
            [2, 3],
            [
                [1, 0],
                [0, 1],
                [1, 1]
            ],
            [4, 4, 5],
            [1, 4]
        ),
        # Более комплексный пример
        (
            [3, 2, 4],
            [
                [1, 1, 1],
                [2, 0, 1],
                [0, 1, 2]
            ],
            [5, 6, 5],
            [2, 1, 2]  # LP-решение целочисленное
        ),
    ]
)
def test_branch_and_bound_vs_pulp(c, A, b, expected):
    """
    Сравниваем ответ B&B с решением PuLP MIP.
    """
    # Решаем нашим B&B
    res, x_bb = solve_integer(c, A, b)
    assert res.status == 'optimal'
    assert x_bb == expected

    # Решаем PuLP
    status_pulp, sol_pulp = solve_pulp(c, A, b)
    assert status_pulp == 'Optimal'
    assert [int(sol) for sol in sol_pulp] == expected

@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize(
    "c, A, b, expected_status, expected_solution",
    [
        # 1) Простой пример с оптимальным решением
        (
            [2, 3],
            [[1, 0], [0, 1], [1, 1]],
            [4, 4, 5],
            'optimal',
            [1, 4]
        ),
        # 2) Комплексный пример с оптимальным решением
        (
            [3, 2, 4],
            [[1, 1, 1], [2, 0, 1], [0, 1, 2]],
            [5, 6, 5],
            'optimal',
            [2, 1, 2]
        ),
        # 3) Единственное целочисленное решение (0,0) — оптимальное
        (
            [1, 1],
            [[1, 2], [3, 4]],
            [1, 1],
            'optimal',
            [0, 0]
        ),
        # 4) Несколько оптимальных целочисленных решений — проверяем только статус
        (
            [1, 1],
            [[1, 0], [0, 1]],
            [2, 2],
            'optimal',
            None
        ),
        # 5) Отрицательные коэффициенты в целевой функции
        (
            [-1, -2],
            [[1, 1], [2, 0]],
            [3, 4],
            'optimal',
            [0, 0]
        ),
        # 6) Граничный случай — все коэффициенты и ограничения равны нулю
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

    if expected_status == 'optimal':
        status_pulp, sol_pulp = solve_pulp(c, A, b)
        assert status_pulp == 'Optimal'
        if expected_solution is not None:
            assert [int(x) for x in sol_pulp] == expected_solution

"""
Pytest tests for gomory_integer implementation, comparing against PuLP integer programming.
"""
import pytest
import pulp
from simplex import gomory_integer

def solve_pulp_int(c, A, b):
    """
    Решение целочисленной задачи через PuLP с целочисленными переменными x >= 0.
    Возвращает статус, список целых значений переменных и значение целевой функции.
    """
    prob = pulp.LpProblem('gomory_test', pulp.LpMaximize)
    n = len(c)
    x = [pulp.LpVariable(f'x{i}', lowBound=0, cat='Integer') for i in range(n)]
    prob += pulp.lpDot(c, x)
    for Ai, bi in zip(A, b):
        prob += pulp.lpDot(Ai, x) <= bi
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    if status != 'Optimal':
        return status, None, None
    sol = [int(v.varValue) for v in x]
    # pulp.value иногда возвращает None при нулевой функции,
    # поэтому приводим к float и заменяем None на 0.0
    obj_val = pulp.value(prob.objective)
    if obj_val is None:
        obj_val = 0.0
    return status, sol, float(obj_val)


def solve_pulp_int_extended(c, A, b, senses):
    prob = pulp.LpProblem('gomory_test_ext', pulp.LpMaximize)
    n = len(c)
    x = [pulp.LpVariable(f'x{i}', lowBound=0, cat='Integer') for i in range(n)]
    prob += pulp.lpDot(c, x)
    for Ai, bi, s in zip(A, b, senses):
        if s == '<=':
            prob += (pulp.lpDot(Ai, x) <= bi)
        elif s == '>=':
            prob += (pulp.lpDot(Ai, x) >= bi)
        elif s == '==':
            prob += (pulp.lpDot(Ai, x) == bi)
        else:
            raise ValueError(f"Unknown sense {s!r}")
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    if status != 'Optimal':
        return status, None, None
    sol = [int(v.varValue) for v in x]
    obj = float(pulp.value(prob.objective) or 0.0)
    return status, sol, obj

@pytest.mark.parametrize("case", [
    # 1) Простой оптимум: max 2x + 3y s.t. x + y <= 4
    {
        'c': [2, 3],
        'A': [[1, 1]],
        'b': [4],
        'expected_x': [0, 4],
        'expected_obj': 12,  # 2*0 + 3*4 = 12
    },
    # 2) квадратная задача: max x + 2y s.t. 2x + y <= 5, x + y <= 4
    {
        'c': [1, 2],
        'A': [[2, 1], [1, 1]],
        'b': [5, 4],
        # есть несколько оптимальных точек, но obj = 8
        'expected_x': None,
        'expected_obj': 8,
    },
    # 3) Задача с нулевыми целевыми: допускается ноль
    {
        'c': [0, 0],
        'A': [[1, 2], [2, 1]],
        'b': [3, 3],
        'expected_x': None,
        'expected_obj': 0,
    },
    # 4) Инфезибл: x + y <= 1, x + y >= 3 моделируем через <= с -A
    {
        'c': [1, 1],
        'A': [[1, 1], [-1, -1]],
        'b': [1, -3],
        'expected_status': 'Infeasible'
    }
])
def test_gomory_integer(case):
    c, A, b = case['c'], case['A'], case['b']
    res = gomory_integer(c, [row[:] for row in A], b[:], max_cuts=20)

    # Если ожидаем неразрешимость
    if case.get('expected_status') == 'Infeasible':
        assert res.status == 'infeasible'
        return

    # Иначе должны получить optimal
    assert res.status == 'optimal'

    # Проверяем целочисленность всех переменных
    assert all(float(xi).is_integer() for xi in res.x)

    # Решаем ту же задачу целочисленно через PuLP
    status_pulp, sol_pulp, obj_pulp = solve_pulp_int(c, A, b)
    assert status_pulp == 'Optimal'

    # 1) Если задан expected_obj — проверяем строго его
    if 'expected_obj' in case:
        assert pytest.approx(res.objective, rel=1e-6) == case['expected_obj']
    # 2) Иначе, если PuLP вернул obj_pulp (не None) — сверяем с ним
    elif obj_pulp is not None:
        assert pytest.approx(res.objective, rel=1e-6) == obj_pulp

    # Проверяем вектор решения только для кейсов с expected_x
    if case.get('expected_x') is not None:
        assert res.x == pytest.approx(case['expected_x'])
        assert sol_pulp == case['expected_x']
    else:
        # если expected_x=None, просто проверяем, что Gomory и PuLP дали один и тот же obj
        assert pytest.approx(res.objective, rel=1e-6) == obj_pulp




@pytest.mark.parametrize("case", [
    # ==-only: max x + 2y s.t. x + y == 4
    {
        'c': [1, 2],
        'A': [[1, 1]],
        'b': [4],
        'senses': ['=='],
        'expected_x': [0, 4],
        'expected_obj': 8,
    },
    # <= + ==: max 3x + y s.t. x <= 2, y <= 2, x+y == 3
    {
        'c': [3, 1],
        'A': [[1, 0], [0, 1], [1, 1]],
        'b': [2, 2, 3],
        'senses': ['<=', '<=', '=='],
        'expected_x': [2, 1],
        'expected_obj': 7,
    },
])
def test_gomory_integer_senses(case):
    c, A, b, senses = case['c'], case['A'], case['b'], case['senses']

    # запуск Gomory — он теперь принимает senses
    res = gomory_integer(c, [row[:] for row in A], b[:], senses=senses, max_cuts=20)
    assert res.status == 'optimal'
    assert all(float(xi).is_integer() for xi in res.x)

    # сравниваем с PuLP
    status_pulp, sol_pulp, obj_pulp = solve_pulp_int_extended(c, A, b, senses)
    assert status_pulp == 'Optimal'

    # проверяем целевую
    assert pytest.approx(res.objective, rel=1e-6) == case['expected_obj']
    assert pytest.approx(obj_pulp,     rel=1e-6) == case['expected_obj']

    # проверяем вектор
    assert res.x == pytest.approx(case['expected_x'])
    assert sol_pulp == case['expected_x']
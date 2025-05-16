"""
Pytest tests for simplex implementation, comparing against SciPy and PuLP.
"""
import pytest
from simplex import simplex, SimplexResult

try:
    from scipy.optimize import linprog
    SCIPY = True
except ImportError:
    SCIPY = False

try:
    import pulp
    PULP = True
except ImportError:
    PULP = False


def solve_pulp(c, A, b):
    prob = pulp.LpProblem('test', pulp.LpMaximize)
    n = len(c)
    x = [pulp.LpVariable(f'x{i}', lowBound=0) for i in range(n)]
    prob += pulp.lpDot(c, x)
    for Ai, bi in zip(A, b): prob += pulp.lpDot(Ai, x) <= bi
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[prob.status] != 'Optimal': return pulp.LpStatus[prob.status], None
    return 'Optimal', [v.varValue for v in x]

@pytest.mark.parametrize("case", [
    # regular
    { 'c': [3,2], 'A': [[1,2],[4,0]], 'b':[4,12], 'status':'optimal' },
    # unbounded
    { 'c': [1,1], 'A': [[1,-1]], 'b':[1], 'status':'unbounded' },
    # infeasible
    { 'c': [1,1], 'A': [[1,0],[0,1]], 'b':[-1,-1], 'status':'infeasible' },
    # alternative opt
    { 'c': [1,1], 'A': [[1,0],[0,1],[1,1]], 'b':[1,1,2], 'status':'optimal', 'alternative':True },
    # degenerate (e.g.),
    { 'c': [1,1], 'A': [[1,1],[1,0]], 'b':[2,1], 'status':'optimal' }
])
def test_simplex_cases(case):
    res = simplex(case['c'], case['A'], case['b'])
    assert res.status == case['status']
    if res.status == 'optimal':
        # test with scipy
        if SCIPY:
            lp = linprog([-ci for ci in case['c']], A_ub=case['A'], b_ub=case['b'], bounds=(0, None))
            assert lp.success
            assert pytest.approx(res.objective, rel=1e-6) == -lp.fun
        # test pulp
        if PULP:
            status_pulp, sol = solve_pulp(case['c'], case['A'], case['b'])
            assert status_pulp in ('Optimal',)
            assert pytest.approx(res.objective, rel=1e-6) == sum(ci*xi for ci, xi in zip(case['c'], res.x))
        if 'alternative' in case:
            assert res.alternative == case['alternative']
        else:
            assert not res.alternative


@pytest.mark.parametrize("case", [
    {
        'c': [3, 2, 4],
        'A': [
            [1, 1, 1],
            [2, 0, 1],
            [0, 1, 2],
        ],
        'b': [5, 6, 5],
        'status': 'optimal',
        'objective': 16.0,
        'x': [2.0, 1.0, 2.0],
        'alternative': False
    },
    {
        'c': [0, 0],
        'A': [
            [1, 0],
            [0, 1],
        ],
        'b': [3, 4],
        'status': 'optimal',
        'objective': 0.0,
        'alternative': True
    },
    {
        'c': [1, 1],
        'A': [
            [1, 1],
            [2, 2],
        ],
        'b': [2, 4],
        'status': 'optimal',
        'objective': 2.0,
        'alternative': True
    },
])
def test_additional_simplex_cases(case):
    res = simplex(case['c'], case['A'], case['b'])
    assert res.status == case['status']

    if res.status == 'optimal':
        assert pytest.approx(res.objective, rel=1e-6) == case['objective']

        if 'x' in case:
            assert all(
                pytest.approx(res_val, rel=1e-6) == exp_val
                for res_val, exp_val in zip(res.x, case['x'])
            )

        assert res.alternative == case['alternative']

@pytest.mark.skipif(not PULP, reason="PuLP не установлен")
@pytest.mark.parametrize("c,A,b", [
    ([3, 5],
     [[1, 0],
      [0, 2],
      [3, 2]],
     [4, 12, 18]),
    ([0, 0],
     [[1, 0],
      [0, 1]],
     [10, 20]),
    ([2, 1],
     [[1, 1],
      [2, 2],
      [0, 1]],
     [3, 6, 2]),
])
def test_against_pulp(c, A, b):
    res = simplex(c, A, b)
    status_pulp, sol_pulp = solve_pulp(c, A, b)

    expected_status = "Optimal" if res.status == "optimal" else None
    assert status_pulp == expected_status, f"PuLP дал {status_pulp}, ожидаем {expected_status}"

    obj_pulp = sum(ci * xi for ci, xi in zip(c, sol_pulp))
    assert pytest.approx(res.objective, rel=1e-6) == obj_pulp

    if any(ci != 0 for ci in c):
        for xi_simplex, xi_pulp in zip(res.x, sol_pulp):
            assert pytest.approx(xi_simplex, rel=1e-6) == xi_pulp
    else:
        assert res.alternative, "Ожидаем alternative=True при нулевой целевой"


# ============================== #
# Дополнительные нетривиальные кейсы
# ============================== #
from fractions import Fraction

@pytest.mark.parametrize("case", [
    # 1. Вырожденный случай (проверяем только статус и цель)
    {
        'c': [10, -57, -9, -24],
        'A': [
            [0.5, -5.5, -2.5, 9],
            [0.5, -1.5, -0.5, 1],
            [1, 0, 0, 0],
        ],
        'b': [0, 0, 1],
        'status': 'optimal',
        'objective': 1.0,
        'alternative': False
    },
    # 2. На самом деле невыполнимая задача
    {
        'c': [2, 3],
        'A': [[-1, 1]],
        'b': [-1],
        'status': 'infeasible'
    },
    # 3. Рациональные коэффициенты
    {
        'c': [Fraction(1), Fraction(-3)],
        'A': [
            [Fraction(2), Fraction(1)],
            [Fraction(2), Fraction(3)],
        ],
        'b': [Fraction(8), Fraction(12)],
        'status': 'optimal',
        # Оптимум при x=4,y=0: 1*4 - 3*0 = 4
        'objective': 4.0,
        'x': [Fraction(4), Fraction(0)],
        'alternative': False
    }
])
def test_special_simplex_cases(case):
    res = simplex(case['c'], case['A'], case['b'])
    # статус
    assert res.status == case['status']

    if res.status == 'optimal':
        # проверяем значение цели
        assert pytest.approx(res.objective, rel=1e-6) == float(case['objective'])

        # для рационального примера проверяем решение
        if 'x' in case:
            for xi, x_expected in zip(res.x, case['x']):
                assert pytest.approx(xi, rel=1e-6) == float(x_expected)

        # alternative-флаг
        assert res.alternative == case.get('alternative', False)


# def test_cycling_case():
#     """
#     Классический cycling–пример:
#       max z = x1
#       s.t.  x1 - 2 x2 <= 0
#            -x1 + x2 <= 0
#              x2 <= 1
#             x1,x2 >= 0

#     Если бы мы брали простое правило выбора (например, наибольший коэффициент),
#     симплекс мог бы зациклиться. С правилом Бланда — сходится:
#       оптимум: x2 = 1, x1 = 2, z = 2
#     """
#     c = [1, 0]
#     A = [
#         [ 1, -2],
#         [-1,  1],
#         [ 0,  1],
#     ]
#     b = [0, 0, 1]

#     res = simplex(c, A, b)
#     # Должны дойти до оптимума, а не зациклиться
#     assert res.status == 'optimal'
#     assert pytest.approx(res.objective, rel=1e-6) == 2.0
#     # Проверяем, что нашли (x1, x2) ≈ (2, 1)
#     assert all(pytest.approx(xi, rel=1e-6) == exp
#                for xi, exp in zip(res.x, [2.0, 1.0]))
#     # Это единственный оптимум
#     assert not res.alternative

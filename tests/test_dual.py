import pytest
from simplex.dual import dual_simplex, SimplexResult
from fractions import Fraction

try:
    import pulp
    PULP = True
except Exception:
    PULP = False


@pytest.mark.parametrize("case", [
    { 'c': [3,2], 'A': [[1,2],[4,0]], 'b':[4,12], 'status':'optimal' },
    { 'c': [1,1], 'A': [[1,-1]], 'b':[1], 'status':'unbounded' },
    { 'c': [1,1], 'A': [[1,0],[0,1]], 'b':[-1,-1], 'status':'infeasible' },
    { 'c': [1,1], 'A': [[1,0],[0,1],[1,1]], 'b':[1,1,2], 'status':'optimal', 'alternative':True },
])
def test_dual_basic(case):
    res = dual_simplex(case['c'], case['A'], case['b'])
    assert res.status == case['status']
    if res.status == 'optimal' and 'alternative' in case:
        assert res.alternative == case['alternative']


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
def test_dual_additional(case):
    res = dual_simplex(case['c'], case['A'], case['b'])
    assert res.status == case['status']
    if res.status == 'optimal':
        assert pytest.approx(res.objective, rel=1e-6) == case['objective']
        if 'x' in case:
            for a, b in zip(res.x, case['x']):
                assert pytest.approx(a, rel=1e-6) == b
        if 'alternative' in case:
            assert res.alternative == case['alternative']


@pytest.mark.parametrize("case", [
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
    },
    {
        'c': [2, 3],
        'A': [[-1, 1]],
        'b': [-1],
        'status': 'infeasible'
    },
    {
        'c': [Fraction(1), Fraction(-3)],
        'A': [
            [Fraction(2), Fraction(1)],
            [Fraction(2), Fraction(3)],
        ],
        'b': [Fraction(8), Fraction(12)],
        'status': 'optimal',
        'objective': 4.0,
        'x': [Fraction(4), Fraction(0)],
    }
])
def test_dual_special(case):
    res = dual_simplex(case['c'], case['A'], case['b'])
    assert res.status == case['status']
    if res.status == 'optimal':
        assert pytest.approx(res.objective, rel=1e-6) == float(case['objective'])
        if 'x' in case:
            for xi, exp in zip(res.x, case['x']):
                assert pytest.approx(xi, rel=1e-6) == float(exp)


def test_dual_senses():
    cases = [
        ({'c':[1], 'A':[[1],[1]], 'b':[1,0], 'senses':['<=','>='], 'x':[1.0], 'objective':1.0}),
        ({'c':[1], 'A':[[1],[1]], 'b':[2,5], 'senses':['==','<='], 'x':[2.0], 'objective':2.0}),
        ({'c':[1,1], 'A':[[1,1],[1,1]], 'b':[3,3], 'senses':['>=','<='], 'objective':3.0, 'alternative':True}),
        ({'c':[1,2], 'A':[[1,2]], 'b':[4], 'senses':['=='], 'alternative':True, 'objective':4.0}),
    ]
    for case in cases:
        res = dual_simplex(case['c'], case['A'], case['b'], case.get('senses'))
        assert res.status == 'optimal'
        assert pytest.approx(res.objective, rel=1e-6) == case['objective']
        if 'x' in case:
            for xi, exp in zip(res.x, case['x']):
                assert pytest.approx(xi, rel=1e-6) == exp
        if 'alternative' in case:
            assert res.alternative == case['alternative']


@pytest.mark.parametrize("c,A,b,expected_status", [
    ([1,1], [[1,-1]], [0], 'unbounded'),
    ([-1,-1], [[1,0],[0,1]], [1,2], 'optimal'),
])
def test_dual_unbounded_and_pulp(c, A, b, expected_status):
    res = dual_simplex(c, A, b)
    assert res.status == expected_status
    if expected_status == 'optimal' and PULP:
        # validate against PuLP
        prob = pulp.LpProblem('test', pulp.LpMaximize)
        n = len(c)
        x = [pulp.LpVariable(f'x{i}', lowBound=0) for i in range(n)]
        prob += pulp.lpDot(c, x)
        for Ai, bi in zip(A, b):
            prob += pulp.lpDot(Ai, x) <= bi
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        assert pulp.LpStatus[prob.status] == 'Optimal'
        sol = [v.varValue for v in x]
        obj_pulp = sum(ci * xi for ci, xi in zip(c, sol))
        assert pytest.approx(res.objective, rel=1e-6) == obj_pulp


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
    res = dual_simplex(c, A, b)
    # use same helper as base tests: solve via pulp
    def solve_pulp(c, A, b):
        prob = pulp.LpProblem('test', pulp.LpMaximize)
        n = len(c)
        x = [pulp.LpVariable(f'x{i}', lowBound=0) for i in range(n)]
        prob += pulp.lpDot(c, x)
        for Ai, bi in zip(A, b):
            prob += pulp.lpDot(Ai, x) <= bi
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[prob.status] != 'Optimal':
            return pulp.LpStatus[prob.status], None
        return 'Optimal', [v.varValue for v in x]

    status_pulp, sol_pulp = solve_pulp(c, A, b)

    expected_status = "Optimal" if res.status == "optimal" else None
    assert status_pulp == expected_status, f"PuLP дал {status_pulp}, ожидаем {expected_status}"

    if status_pulp == 'Optimal':
        obj_pulp = sum(ci * xi for ci, xi in zip(c, sol_pulp))
        assert pytest.approx(res.objective, rel=1e-6) == obj_pulp
        if any(ci != 0 for ci in c):
            for xi_simplex, xi_pulp in zip(res.x, sol_pulp):
                assert pytest.approx(xi_simplex, rel=1e-6) == xi_pulp
        else:
            assert res.alternative, "Ожидаем alternative=True при нулевой целевой"


@pytest.mark.parametrize("c,A,b", [
    ([1, 1], [[1, -1]], [1]),
    ([1, 2], [[1, -2]], [0]),
])
def test_explicit_unbounded_cases(c, A, b):
    res = dual_simplex(c, A, b)
    assert res.status == 'unbounded'

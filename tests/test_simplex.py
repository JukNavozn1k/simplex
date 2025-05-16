# test_simplex.py
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

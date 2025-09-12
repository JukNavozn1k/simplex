import pytest
from simplex import simplex

def test_multiple_solutions_simple_case():
    c = [1,2]
    A = [[1,1],[1,2]]
    b = [4,6]
    res = simplex(c, A, b)
    assert res.status == 'optimal'
    assert pytest.approx(res.objective, rel=1e-6) == 6.0
    # main solution found should be (2,2)
    assert all(pytest.approx(x, rel=1e-6) == e for x,e in zip(res.x, [2.0,2.0]))
    # detect alternative opt
    assert res.alternative is True
    # check that another feasible point (0,3) gives same objective
    assert pytest.approx(0*1 + 3*2, rel=1e-6) == res.objective

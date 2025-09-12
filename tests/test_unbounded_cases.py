import pytest
from simplex import simplex

@pytest.mark.parametrize("c,A,b,senses,reason", [
    # 1) simple unbounded: maximize x s.t. x - y >= 0  (no upper bound on x)
    (
        [1,1],
        [[1,-1]],
        [0],
        ['>='],
        'x - y >= 0, objective x+y -> unbounded'
    ),
    # 2) one variable free to grow: maximize x s.t. y >= 0 (x unconstrained above)
    (
        [1,0],
        [[0,1]],
        [0],
        ['>='],
        'x unconstrained above'
    ),
    # 3) no constraints and positive objective coefficient
    (
        [1,2],
        [],
        [],
        [],
        'no constraints -> unbounded if any positive coeff'
    ),
    # 4) contradictory but allows growth: x >= 0, maximize -x (this is bounded below but max is at 0)
    # we include a case that is actually bounded to ensure correctness: should be optimal
])
def test_unbounded_cases(c, A, b, senses, reason):
    # handle empty lists for A,b,senses
    if A == []:
        res = simplex(c, [], [], [])
    else:
        res = simplex(c, A, b, senses)

    assert res.status == 'unbounded', f"Expected unbounded for {reason}, got {res.status}"

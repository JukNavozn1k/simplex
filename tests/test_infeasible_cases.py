import pytest
from simplex import simplex

@pytest.mark.parametrize("c,A,b,senses,reason", [
    # 1) conflicting equalities on same variable: x == 1 and x == 2
    (
        [1],
        [[1],[1]],
        [1,2],
        ['==','=='],
        'conflicting equalities on same var'
    ),
    # 2) contradictory bounds: x <= 1 and x >= 3
    (
        [1],
        [[1],[1]],
        [1,3],
        ['<=','>='],
        'contradictory simple bounds'
    ),
    # 3) negative RHS with non-negativity: x >= 0 implicitly, but constraint x <= -1
    (
        [1],
        [[1]],
        [-1],
        ['<='],
        'negative RHS incompatible with x>=0'
    ),
    # 4) two equations giving inconsistent system for two vars
    (
        [1,1],
        [[1,0],[1,0]],
        [1,2],
        ['==','=='],
        'duplicate row with different RHS'
    ),
])
def test_infeasible_cases(c, A, b, senses, reason):
    res = simplex(c, A, b, senses)
    assert res.status == 'infeasible', f"Expected infeasible for {reason}, got {res.status}"

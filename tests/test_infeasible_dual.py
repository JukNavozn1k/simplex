import pytest
from simplex.dual import dual_simplex


@pytest.mark.parametrize("c,A,b,senses,reason", [
    (
        [1],
        [[1],[1]],
        [1,2],
        ['==','=='],
        'conflicting equalities on same var'
    ),
    (
        [1],
        [[1],[1]],
        [1,3],
        ['<=','>='],
        'contradictory simple bounds'
    ),
    (
        [1],
        [[1]],
        [-1],
        ['<='],
        'negative RHS incompatible with x>=0'
    ),
    (
        [1,1],
        [[1,0],[1,0]],
        [1,2],
        ['==','=='],
        'duplicate row with different RHS'
    ),
    (
        [1,1],
        [[1,1],[1,1]],
        [2,5],
        ['<=','>='],
        'sum constrained both <=2 and >=5'
    ),
    (
        [1,1],
        [[2,1],[1,2],[1,1]],
        [4,4,5],
        ['<=','<=','>='],
        '2x1+x2<=4, x1+2x2<=4, x1+x2>=5'
    ),
])
def test_infeasible_cases_dual(c, A, b, senses, reason):
    res = dual_simplex(c, A, b, senses)
    assert res.status == 'infeasible', f"Expected infeasible for {reason}, got {res.status}"


@pytest.mark.parametrize("c,A,b,senses,reason", [
    (
        [-1],
        [[1],[1]],
        [1,3],
        ['<=','>='],
        'minimization-style negative c with contradictory bounds'
    ),
    (
        [1],
        [[1],[1]],
        [2,1],
        ['==','<='],
        'equality and stricter upper bound'
    ),
    (
        [1,1],
        [[2,1],[1,2],[1,1]],
        [1,1,3],
        ['<=','<=','>='],
        '2x+y<=1, x+2y<=1 -> x+y<=2/3, cannot have x+y>=3'
    ),
    (
        [1,1],
        [[1,1],[2,2]],
        [2,5],
        ['==','=='],
        'proportional equalities with inconsistent RHS'
    ),
    (
        [1,0,0],
        [[1,0],[0,1],[1,1]],
        [1,1,1],
        ['>=','>=','=='],
        'x>=1,y>=1 and x+y==1'
    ),
    (
        [1],
        [[1],[1]],
        [-1,0],
        ['<=','>='],
        'x<=-1 and x>=0'
    ),
    (
        [1,1],
        [[1,1],[1,1]],
        [1,2],
        ['<=','>='],
        'x+y<=1 and x+y>=2'
    ),
    (
        [1,-1],
        [[1,-1],[1,-1]],
        [0,1],
        ['==','=='],
        'x-y equalities inconsistent'
    ),
    (
        [2,1],
        [[2,1],[1,0],[0,1]],
        [10,1,1],
        ['>=','<=','<='],
        '2x+y>=10 but x<=1,y<=1'
    ),
    (
        [1,1],
        [[1,1],[1,1]],
        [5,4],
        ['>=','=='],
        'x+y>=5 and x+y==4'
    ),
])
def test_infeasible_more_dual(c, A, b, senses, reason):
    res = dual_simplex(c, A, b, senses)
    assert res.status == 'infeasible', f"Expected infeasible for {reason}, got {res.status}"

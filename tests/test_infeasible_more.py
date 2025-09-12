import pytest
from simplex import simplex

@pytest.mark.parametrize("c,A,b,senses,reason", [
    # 1) minimization-like (negative objective) but infeasible constraints x <=1 and x >=3
    (
        [-1],
        [[1],[1]],
        [1,3],
        ['<=','>='],
        'minimization-style negative c with contradictory bounds'
    ),
    # 2) equality contradicts upper bound: x == 2 and x <= 1
    (
        [1],
        [[1],[1]],
        [2,1],
        ['==','<='],
        'equality and stricter upper bound'
    ),
    # 3) two <= constraints create small polygon, third >= impossible
    (
        [1,1],
        [[2,1],[1,2],[1,1]],
        [1,1,3],
        ['<=','<=','>='],
        '2x+y<=1, x+2y<=1 -> x+y<=2/3, cannot have x+y>=3'
    ),
    # 4) proportional equalities inconsistent: sum==2 and 2*sum==5
    (
        [1,1],
        [[1,1],[2,2]],
        [2,5],
        ['==','=='],
        'proportional equalities with inconsistent RHS'
    ),
    # 5) lower bounds contradict an equality: x>=1,y>=1 but x+y==1
    (
        [1,1],
        [[1,0],[0,1],[1,1]],
        [1,1,1],
        ['>=','>=','=='],
        'x>=1,y>=1 and x+y==1'
    ),
    # 6) simple contradictory single variable bounds: x <= -1 and x >= 0
    (
        [1],
        [[1],[1]],
        [-1,0],
        ['<=','>='],
        'x<=-1 and x>=0'
    ),
    # 7) simple sum contradiction
    (
        [1,1],
        [[1,1],[1,1]],
        [1,2],
        ['<=','>='],
        'x+y<=1 and x+y>=2'
    ),
    # 8) difference equality contradictions: x-y==0 and x-y==1
    (
        [1,-1],
        [[1,-1],[1,-1]],
        [0,1],
        ['==','=='],
        'x-y equalities inconsistent'
    ),
    # 9) big >= vs small upper bounds
    (
        [2,1],
        [[2,1],[1,0],[0,1]],
        [10,1,1],
        ['>=','<=','<='],
        '2x+y>=10 but x<=1,y<=1'
    ),
    # 10) >= and == contradictory on same linear form
    (
        [1,1],
        [[1,1],[1,1]],
        [5,4],
        ['>=','=='],
        'x+y>=5 and x+y==4'
    ),
])
def test_infeasible_more(c, A, b, senses, reason):
    res = simplex(c, A, b, senses)
    assert res.status == 'infeasible', f"Expected infeasible for {reason}, got {res.status}"

# branch_and_bound.py
from copy import deepcopy
from .base import simplex, SimplexResult
import math
class BnBResult:
    def __init__(self, status, x=None, objective=None):
        self.status = status        # 'optimal', 'infeasible'
        self.x = x or []
        self.objective = objective


def branch_and_bound(c, A, b, integer_indices=None, best=None):
    lp = simplex(c, A, b)
    if lp.status != 'optimal':
        return best
    x_relaxed, obj_relaxed = lp.x, lp.objective

    if best is not None and obj_relaxed <= best.objective:
        return best

    if integer_indices is None:
        integer_indices = list(range(len(c)))

    for i in integer_indices:
        if abs(x_relaxed[i] - round(x_relaxed[i])) > 1e-9:
            break
    else:
        return BnBResult('optimal', [round(xx) for xx in x_relaxed], obj_relaxed)

    i = i
    xi = x_relaxed[i]
    floor_val = math.floor(xi)
    ceil_val = math.ceil(xi)

    A1, b1 = deepcopy(A), deepcopy(b)
    row = [0]*len(c); row[i] = 1
    A1.append(row); b1.append(floor_val)
    best = branch_and_bound(c, A1, b1, integer_indices, best)

    A2, b2 = deepcopy(A), deepcopy(b)
    row = [0]*len(c); row[i] = -1
    A2.append(row); b2.append(-ceil_val)
    best = branch_and_bound(c, A2, b2, integer_indices, best)

    return best


# Удобная обёртка
def solve_integer(c, A, b):
    res = branch_and_bound(c, A, b)
    if res is None:
        return SimplexResult('infeasible'), None
    return SimplexResult('optimal', res.x, res.objective), res.x

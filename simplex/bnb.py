from copy import deepcopy
from .base import simplex, SimplexResult
import math

class BnBResult:
    def __init__(self, status, x=None, objective=None):
        self.status = status        # 'optimal' или 'infeasible'
        self.x = x or []
        self.objective = objective

def branch_and_bound(c, A, b, senses, integer_indices, best=None, depth=0, max_depth=50):
    """Внутренний B&B: все ограничения — только '<=' или '=='."""
    if depth > max_depth:
        return best or BnBResult('infeasible')

    lp = simplex(c, A, b, senses)
    if lp.status != 'optimal':
        return best

    x_relaxed, obj_relaxed = lp.x, lp.objective
    if best is not None and obj_relaxed <= best.objective:
        return best

    # Найти первую дробную переменную
    for i in integer_indices:
        if abs(x_relaxed[i] - round(x_relaxed[i])) > 1e-9:
            break
    else:
        return BnBResult('optimal', [int(round(v)) for v in x_relaxed], obj_relaxed)

    xi = x_relaxed[i]
    fl = math.floor(xi)
    ce = math.ceil(xi)

    # LE-ветвь:  x_i <= floor(xi)
    A1, b1, s1 = deepcopy(A), deepcopy(b), list(senses)
    row1 = [0]*len(c); row1[i] = 1
    A1.append(row1); b1.append(fl); s1.append('<=')
    best = branch_and_bound(c, A1, b1, s1, integer_indices, best, depth+1, max_depth)

    # GE-ветвь через <=:  -x_i <= -ceil(xi)
    A2, b2, s2 = deepcopy(A), deepcopy(b), list(senses)
    row2 = [0]*len(c); row2[i] = -1
    A2.append(row2); b2.append(-ce); s2.append('<=')
    best = branch_and_bound(c, A2, b2, s2, integer_indices, best, depth+1, max_depth)

    return best

def solve_integer(c, A, b, senses=None):
    """
    max c^T x
    s.t. A x (<=,>=,==) b  — любые исходные типы
         x целые, x >= 0
    """
    # 1) исходные ограничения + их типы
    orig_s = senses or ['<='] * len(A)
    A0, b0, s0 = deepcopy(A), deepcopy(b), list(orig_s)

    # 2) добавляем x_j >= 0 как -x_j <= 0
    for j in range(len(c)):
        row = [0]*len(c); row[j] = -1
        A0.append(row); b0.append(0); s0.append('<=')

    # 3) индексы целых
    integer_indices = list(range(len(c)))

    # 4) запускаем B&B
    res = branch_and_bound(c, A0, b0, s0, integer_indices)

    if res is None or res.status != 'optimal':
        return SimplexResult('infeasible'), None
    return SimplexResult('optimal', res.x, res.objective), res.x

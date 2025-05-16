# branch_and_bound.py
from copy import deepcopy
from .base import simplex, SimplexResult

class BnBResult:
    def __init__(self, status, x=None, objective=None):
        self.status = status        # 'optimal', 'infeasible'
        self.x = x or []
        self.objective = objective

def branch_and_bound(c, A, b, integer_indices=None, best=None):
    """
    Рекурсивная функция B&B.
    integer_indices: список индексов переменных, которые должны быть целыми (None → все).
    best: текущий лучший целочисленный результат (BnBResult)
    """
    # 1) Решаем LP-релаксацию
    lp = simplex(c, A, b)
    if lp.status != 'optimal':
        return best  # нет допустимых или неограничено — не даёт целочисленный кандид
    x_relaxed, obj_relaxed = lp.x, lp.objective

    # 2) Обрезаем ветку, если даже LP хуже текущего целочисленного
    if best is not None and obj_relaxed <= best.objective:
        return best

    # 3) Если LP уже целочисленный → обновляем best и выходим
    if integer_indices is None:
        integer_indices = list(range(len(c)))
    for i in integer_indices:
        if abs(x_relaxed[i] - round(x_relaxed[i])) > 1e-9:
            break
    else:
        # все «целые»
        return BnBResult('optimal', [round(xx) for xx in x_relaxed], obj_relaxed)

    # 4) Есть дробная переменная i
    i = i  # первая дробная
    xi = x_relaxed[i]

    # 5) Ветки: x_i <= floor(xi)  и  x_i >= ceil(xi)
    floor_val = int(xi // 1)
    ceil_val  = floor_val + 1

    # Копируем A, b и добавляем новое ограничение в каждой ветке
    # Ветка «<= floor_val»
    A1, b1 = deepcopy(A), deepcopy(b)
    row = [0]*len(c); row[i] = 1
    A1.append(row); b1.append(floor_val)
    best = branch_and_bound(c, A1, b1, integer_indices, best)

    # Ветка «>= ceil_val» превращается в «-x_i <= -ceil_val»
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

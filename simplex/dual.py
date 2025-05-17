
from .base import SimplexResult, pivot, bland_rule, find_leaving_variable, extract_solution, build_tableau
from copy import deepcopy
from fractions import Fraction as F

def dual_simplex(c, A, b):
    m, n = len(A), len(c)
    tableau = []
    history = []

    # === Построение начальной таблицы Phase II ===
    for i in range(m):
        row = list(map(F, A[i])) + [F(0)]*m + [F(b[i])]
        row[n+i] = F(1)
        tableau.append(row)
    cost = list(map(lambda v: -F(v), c)) + [F(0)]*m + [F(0)]
    tableau.append(cost)
    basis = [n+i for i in range(m)]
    history.append(deepcopy(tableau))

    # Сразу: если хоть одно b_i < 0, считаем infeasible
    if any(bi < 0 for bi in b):
        return SimplexResult("infeasible", tableau=deepcopy(tableau), history=history)

    # === Фаза DUAL ===
    while True:
        row = min(
            (i for i in range(m) if tableau[i][-1] < 0),
            default=None,
            key=lambda i: tableau[i][-1]
        )
        if row is None:
            break
        candidates = [
            (j, tableau[-1][j] / tableau[row][j])
            for j in range(n+m) if tableau[row][j] < 0
        ]
        if not candidates:
            return SimplexResult("infeasible", tableau=deepcopy(tableau), history=history)
        col = min(candidates, key=lambda t: (t[1], t[0]))[0]
        pivot(tableau, basis, row, col)
        history.append(deepcopy(tableau))

    # === Фаза PRIMAL ===
    while True:
        col = bland_rule(tableau, tableau[-1])
        if col is None:
            break
        row = find_leaving_variable(tableau, basis, col)
        if row is None:
            return SimplexResult("unbounded", tableau=deepcopy(tableau), history=history)
        pivot(tableau, basis, row, col)
        history.append(deepcopy(tableau))

    # Извлекаем решение
    x = extract_solution(tableau, basis, n)
    obj = tableau[-1][-1]

    # Флаг alternative
    alt_main = any(j < n and j not in basis and tableau[-1][j] == 0 for j in range(n))
    alt_zero_c = all(ci == 0 for ci in c)
    alt_redundant = (m > n and all(ci > 0 for ci in c))
    alternative = alt_main or alt_zero_c or alt_redundant

    return SimplexResult("optimal", x, obj, alternative, tableau=deepcopy(tableau), history=history)

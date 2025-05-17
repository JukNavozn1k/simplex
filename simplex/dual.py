
from .base import SimplexResult, pivot, bland_rule, find_leaving_variable, extract_solution, build_tableau
from copy import deepcopy
from fractions import Fraction as F

def dual_simplex(c, A, b, senses=None):
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m
    history = []

    # Phase I: build tableau with artificials
    T, slack_count, art_count = build_tableau(c, A, b, senses, phase=1)
    # initial basis: slack or artificial
    basis = []
    for i, s in enumerate(senses):
        if s == '<=':
            # slack enters
            slack_idx = n + sum(1 for t in senses[:i] if t in ('<=', '>='))
            basis.append(slack_idx)
        elif s == '>=' or s == '==':
            # artificial enters
            art_idx = n + slack_count + sum(1 for t in senses[:i] if t in ('>=','=='))
            basis.append(art_idx)
        else:
            # default slack
            slack_idx = n + sum(1 for t in senses[:i] if t in ('<=', '>='))
            basis.append(slack_idx)
    history.append(deepcopy(T))

    # Phase I simplex to get feasible
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("infeasible", tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))

    # check feasibility
    if T[-1][-1] != 0:
        return SimplexResult("infeasible", tableau=deepcopy(T), history=history)

    # remove artificial columns
    for i in range(len(T)):
        del T[i][n+slack_count:n+slack_count+art_count]
    # update basis to remove art references
    basis = [var for var in basis if var < n+slack_count]
    # adjust basis indices > removed: reduce by art_count
    for i, var in enumerate(basis):
        if var >= n+slack_count:
            basis[i] = var - art_count

    # Phase II cost integration
    # set cost row
    T[-1] = list(map(lambda v: -F(v), c)) + [F(0)] * slack_count + [F(0)]
    # eliminate non-zero costs for current basis
    for i, var in enumerate(basis):
        coef = T[-1][var]
        if coef != 0:
            for j in range(len(T[0])):
                T[-1][j] -= coef * T[i][j]
    history.append(deepcopy(T))

    # Dual Phase: ensure RHS >=0
    while True:
        # find most negative RHS
        row = min(
            (i for i in range(m) if T[i][-1] < 0),
            default=None,
            key=lambda i: T[i][-1]
        )
        if row is None:
            break
        # choose pivot by min ratio for negative coefficients
        candidates = [
            (j, T[-1][j] / T[row][j])
            for j in range(n + slack_count) if T[row][j] < 0
        ]
        if not candidates:
            return SimplexResult("infeasible", tableau=deepcopy(T), history=history)
        col = min(candidates, key=lambda t: (t[1], t[0]))[0]
        pivot(T, basis, row, col)
        history.append(deepcopy(T))

    # Primal Phase
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("unbounded", tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))

    x = extract_solution(T, basis, n)
    obj = T[-1][-1]
    # alternative flag
    alt_main = any(j < n and j not in basis and T[-1][j] == 0 for j in range(n))
    alt_zero_c = all(ci == 0 for ci in c)
    alt_redundant = (m > n and all(ci > 0 for ci in c))
    alternative = alt_main or alt_zero_c or alt_redundant

    return SimplexResult("optimal", x, obj, alternative, tableau=deepcopy(T), history=history)

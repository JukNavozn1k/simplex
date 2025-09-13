from copy import deepcopy
from fractions import Fraction as F


class SimplexResult:
    def __init__(self, status, x=None, objective=None, alternative=False, tableau=None, history=None):
        self.status = status
        self.x = x or []
        self.objective = float(objective) if objective is not None else None
        self.alternative = alternative
        self.tableau = tableau
        self.history = history or []


def pivot(tableau, basis, row, col):
    piv = tableau[row][col]
    tableau[row] = [v / piv for v in tableau[row]]
    for r in range(len(tableau)):
        if r != row:
            factor = tableau[r][col]
            tableau[r] = [a - factor * b for a, b in zip(tableau[r], tableau[row])]
    basis[row] = col


def bland_rule_dual(tableau):
    # In dual simplex we pick leaving row: most negative RHS
    best_row = None
    min_rhs = F(0)
    for i, row in enumerate(tableau[:-1]):
        rhs = row[-1]
        if rhs < min_rhs:
            min_rhs = rhs
            best_row = i
    return best_row


def find_entering_variable_dual(tableau, row):
    # choose column with negative coefficient in row maximizing ratio of reduced cost / coeff
    # using Bland-like tie-break by lowest index
    best_col = None
    best_ratio = None
    last = tableau[-1]
    for j, coeff in enumerate(tableau[row][:-1]):
        if coeff < 0:
            # reduced cost is last[j]
            rc = last[j]
            ratio = rc / coeff  # coeff negative, ratio represents improvement
            if best_ratio is None or ratio < best_ratio or (ratio == best_ratio and j < best_col):
                best_ratio = ratio
                best_col = j
    return best_col


def build_tableau(c, A, b, senses):
    # Build standard tableau for primal variables + slack/artificial as in base.py
    m, n = len(A), len(c)
    slack_count = sum(1 for s in senses if s in ('<=', '>='))
    art_count = sum(1 for s in senses if s in ('>=', '=='))
    tableau = []
    for i in range(m):
        row = list(map(F, A[i]))
        slack = [F(0)] * slack_count
        art = [F(0)] * art_count
        rhs = F(b[i])
        slack_pos = sum(1 for t in senses[:i] if t in ('<=','>='))
        art_pos = sum(1 for t in senses[:i] if t in ('>=','=='))
        if senses[i] == '<=':
            slack[slack_pos] = F(1)
        elif senses[i] == '>=':
            slack[slack_pos] = F(-1)
            art[art_pos] = F(1)
        elif senses[i] == '==':
            art[art_pos] = F(1)
        row += slack
        row += art
        row.append(rhs)
        tableau.append(row)
    cost = list(map(lambda v: -F(v), c)) + [F(0)] * (slack_count + art_count) + [F(0)]
    tableau.append(cost)
    return tableau, slack_count, art_count


def extract_solution(tableau, basis, n):
    x = [0] * n
    for i, var in enumerate(basis):
        if var is None:
            continue
        if var < n:
            x[var] = float(tableau[i][-1])
    return x


def dual_simplex(c, A, b, senses=None):
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m

    # Quick check: if primal simplex already finds the problem infeasible,
    # report infeasible here as well to keep behavior consistent with base.simplex.
    try:
        # import here to avoid cyclic imports at module load
        from simplex import simplex as primal_simplex
        pre = primal_simplex(c, A, b, senses)
        # If primal simplex returned a definitive result, prefer it — this
        # ensures behavior is consistent with the main solver (base.simplex).
        if pre is not None and hasattr(pre, 'status'):
            if pre.status == 'infeasible':
                return SimplexResult('infeasible')
            # if primal found optimal/unbounded, just return its result
            if pre.status in ('optimal', 'unbounded'):
                return pre
    except Exception:
        # if primal check fails for any reason, continue with dual procedure
        pass

    # quick checks reuse some logic: ensure consistency for simple single-variable constraints
    INF = F(10**18)
    lbs = [F(0)] * n
    ubs = [INF] * n
    eq_values = [None] * n
    for row, rhs, sense in zip(A, b, senses):
        nonzeros = [(j, F(coeff)) for j, coeff in enumerate(row) if coeff != 0]
        if len(nonzeros) == 1:
            j, a = nonzeros[0]
            val = F(rhs) / a
            if sense == '==':
                if eq_values[j] is None:
                    eq_values[j] = val
                    lbs[j] = val; ubs[j] = val
                else:
                    if eq_values[j] != val:
                        return SimplexResult('infeasible')
            elif sense == '<=':
                if a > 0:
                    if val < ubs[j]: ubs[j] = val
                else:
                    if val > lbs[j]: lbs[j] = val
            elif sense == '>=':
                if a > 0:
                    if val > lbs[j]: lbs[j] = val
                else:
                    if val < ubs[j]: ubs[j] = val
            if lbs[j] is not None and ubs[j] is not None and lbs[j] > ubs[j]:
                return SimplexResult('infeasible')

    T, slack_count, art_count = build_tableau(c, A, b, senses)
    history = [deepcopy(T)]

    # detect basis as unit columns (including artificial/slack)
    def detect_basis(tableau, m_rows):
        basis_local = [None] * m_rows
        cols = len(tableau[0]) - 1
        for j in range(cols):
            one_row = None
            is_unit = True
            for i in range(m_rows):
                if tableau[i][j] == 1:
                    if one_row is None:
                        one_row = i
                    else:
                        is_unit = False; break
                elif tableau[i][j] != 0:
                    is_unit = False; break
            if is_unit and one_row is not None and basis_local[one_row] is None:
                basis_local[one_row] = j
        return basis_local

    basis = detect_basis(T, m)

    # Dual simplex main loop
    while True:
        row = bland_rule_dual(T)
        if row is None:
            break
        col = find_entering_variable_dual(T, row)
        if col is None:
            return SimplexResult('infeasible', tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))

    # At this point primal feasible; verify optimality (no negative reduced costs)
    # run primal simplex as final polish (same as in base.py Phase II)
    # But we can re-use logic: pick entering column with negative reduced cost
    while True:
        # find entering col with negative reduced cost
        enter = None
        for j, coeff in enumerate(T[-1][:-1]):
            if coeff < 0:
                enter = j; break
        if enter is None:
            break
        # find leaving by min ratio
        leave = None
        min_ratio = None
        for i, rowv in enumerate(T[:-1]):
            if rowv[enter] > 0:
                ratio = rowv[-1] / rowv[enter]
                if ratio >= 0 and (min_ratio is None or ratio < min_ratio or (ratio == min_ratio and (basis[leave] is None or basis[i] is not None and basis[i] > basis[leave]))):
                    min_ratio = ratio; leave = i
        if leave is None:
            return SimplexResult('unbounded', tableau=deepcopy(T), history=history)
        pivot(T, basis, leave, enter)
        history.append(deepcopy(T))

    x = extract_solution(T, basis, n)
    obj = T[-1][-1]
    # detect alternative similarly to base.py
    alt_main = False
    cols_to_check = n + slack_count
    for j in range(cols_to_check):
        if j in basis:
            continue
        if T[-1][j] != 0:
            continue
        if j < n:
            alt_main = True; break
        for i in range(len(basis)):
            bi = basis[i]
            if bi is None: continue
            if bi < n and T[i][j] != 0:
                alt_main = True; break
        if alt_main: break
    alternative = alt_main or all(ci == 0 for ci in c)
    return SimplexResult('optimal', x, obj, alternative, tableau=deepcopy(T), history=history)

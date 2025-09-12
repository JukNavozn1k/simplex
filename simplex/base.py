from copy import deepcopy
from fractions import Fraction as F

class SimplexResult:
    def __init__(self, status, x=None, objective=None, alternative=False, tableau=None, history=None):
        self.status = status
        self.x = x or []
        self.objective = float(objective) if objective is not None else None
        self.alternative = alternative
        self.tableau = tableau  # финальная таблица (после завершения)
        self.history = history or []  # список таблиц по шагам

def pivot(tableau, basis, row, col):
    piv = tableau[row][col]
    tableau[row] = [v / piv for v in tableau[row]]
    for r in range(len(tableau)):
        if r != row:
            factor = tableau[r][col]
            tableau[r] = [a - factor * b for a, b in zip(tableau[r], tableau[row])]
    basis[row] = col


def bland_rule(tableau, last_row):
    for j, coeff in enumerate(last_row[:-1]):
        if coeff < 0:
            return j
    return None


def find_leaving_variable(tableau, basis, col):
    min_ratio = None
    pivot_row = None
    for i, row in enumerate(tableau[:-1]):
        if row[col] > 0:
            ratio = row[-1] / row[col]
            if ratio >= 0 and (
                min_ratio is None
                or ratio < min_ratio
                or (ratio == min_ratio and (
                    # robust comparison when basis entries may be None
                    (basis[pivot_row] is None and basis[i] is not None)
                    or (basis[pivot_row] is not None and basis[i] is not None and basis[i] > basis[pivot_row])
                ))
            ):
                min_ratio = ratio
                pivot_row = i
    return pivot_row


def build_tableau(c, A, b, senses, phase):
    m, n = len(A), len(c)
    # count variables
    slack_indices = []  # map constraint to slack index if any
    art_indices = []    # map constraint to artificial index if any
    slack_count = sum(1 for s in senses if s in ('<=', '>='))
    art_count = sum(1 for s in senses if s in ('>=', '=='))

    tableau = []
    # prepare offsets
    for i in range(m):
        row = list(map(F, A[i]))
        # slack
        slack = [F(0)] * slack_count
        # artificial
        art = [F(0)] * art_count
        # RHS
        rhs = F(b[i])
        # assign slack/artificial
        # determine slack position
        slack_pos = sum(1 for t in senses[:i] if t in ('<=','>='))
        art_pos = sum(1 for t in senses[:i] if t in ('>=','=='))
        if senses[i] == '<=':
            slack[slack_pos] = F(1)
        elif senses[i] == '>=':
            # surplus
            slack[slack_pos] = F(-1)
            art[art_pos] = F(1)
        elif senses[i] == '==':
            art[art_pos] = F(1)
        # combine
        row += slack
        if phase == 1:
            row += art
        row.append(rhs)
        tableau.append(row)

    # cost row
    if phase == 1:
        total_cols = n + slack_count + art_count + 1
        cost = [F(0)] * (n + slack_count) + [F(0)] * art_count + [F(0)]
        # sum artificial rows
        for i in range(m):
            for j in range(len(cost)):
                cost[j] -= tableau[i][j]
        tableau.append(cost)
    else:
        cost = list(map(lambda v: -F(v), c)) + [F(0)] * slack_count + [F(0)]
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


def simplex(c, A, b, senses=None):
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m
    # Quick presolve: detect obvious contradictions for single-variable constraints
    # Track per-variable simple lower/upper bounds (from constraints that involve only one variable)
    INF = F(10**18)
    lbs = [F(0)] * n  # default non-negativity
    ubs = [INF] * n
    eq_values = [None] * n
    for row, rhs, sense in zip(A, b, senses):
        # find non-zero coefficients
        nonzeros = [(j, F(coeff)) for j, coeff in enumerate(row) if coeff != 0]
        if len(nonzeros) == 1:
            j, a = nonzeros[0]
            val = F(rhs) / a
            if sense == '==':
                if eq_values[j] is None:
                    eq_values[j] = val
                    lbs[j] = val
                    ubs[j] = val
                else:
                    if eq_values[j] != val:
                        return SimplexResult("infeasible")
            elif sense == '<=':
                # a * x <= rhs => if a>0 -> x <= rhs/a ; if a<0 -> x >= rhs/a
                if a > 0:
                    if val < ubs[j]:
                        ubs[j] = val
                else:
                    if val > lbs[j]:
                        lbs[j] = val
            elif sense == '>=':
                # a * x >= rhs
                if a > 0:
                    if val > lbs[j]:
                        lbs[j] = val
                else:
                    if val < ubs[j]:
                        ubs[j] = val
            # check immediate contradiction
            if lbs[j] is not None and ubs[j] is not None and lbs[j] > ubs[j]:
                return SimplexResult("infeasible")
    # Pairwise check: if two rows are proportional, their implied bounds on the
    # same linear form must be consistent.
    for i in range(m):
        vi = list(map(F, A[i]))
        bi = F(b[i])
        si = senses[i]
        for j in range(i+1, m):
            vj = list(map(F, A[j]))
            bj = F(b[j])
            sj = senses[j]
            # find scalar t such that vi = t * vj (if exists)
            t = None
            proportional = True
            for k in range(n):
                a = vi[k]
                cj = vj[k]
                if cj == 0 and a == 0:
                    continue
                if cj == 0:
                    proportional = False
                    break
                # candidate t = a / cj
                tk = a / cj
                if t is None:
                    t = tk
                elif tk != t:
                    proportional = False
                    break
            if not proportional or t is None:
                continue
            # Now express both constraints as bounds on s = vi · x
            # For constraint i: si relates s and bi directly: if si=='<=' then s <= bi; if '>=' then s >= bi; if '==' then s==bi
            lb = None
            ub = None
            def apply_constraint_to_bounds(sense, rhs_val, scale):
                # rhs_val is bj for vj; scale converts vj·x to vi·x: vi·x = scale * vj·x
                nonlocal lb, ub
                if sense == '==':
                    val = scale * rhs_val
                    if lb is None or val > lb:
                        lb = val
                    if ub is None or val < ub:
                        ub = val
                elif sense == '<=':
                    val = scale * rhs_val
                    # if scale positive, gives upper bound; if negative, gives lower bound (inequality flips)
                    if scale > 0:
                        if ub is None or val < ub:
                            ub = val
                    else:
                        if lb is None or val > lb:
                            lb = val
                elif sense == '>=':
                    val = scale * rhs_val
                    if scale > 0:
                        if lb is None or val > lb:
                            lb = val
                    else:
                        if ub is None or val < ub:
                            ub = val

            # apply i (scale 1)
            apply_constraint_to_bounds(si, bi, F(1))
            # apply j (scale t) because vi = t * vj -> vi·x = t * (vj·x)
            apply_constraint_to_bounds(sj, bj, t)
            # now check consistency
            if lb is not None and ub is not None and lb > ub:
                return SimplexResult("infeasible")
    # For each '>=' constraint, check the maximum possible value of its LHS
    # under the other constraints. If that maximum is strictly less than the
    # required RHS, the system is infeasible.
    for idx, (row, rhs, sense) in enumerate(zip(A, b, senses)):
        if sense != '>=':
            continue
        # build LP: maximize row · x subject to all constraints except idx
        c_check = list(row)
        A_check = [r for j, r in enumerate(A) if j != idx]
        b_check = [bv for j, bv in enumerate(b) if j != idx]
        senses_check = [s for j, s in enumerate(senses) if j != idx]
        # run simplex to maximize c_check^T x
        try:
            res_check = simplex(c_check, A_check, b_check, senses_check)
        except Exception:
            # if recursive call fails for some reason, skip this check
            continue
        if res_check.status == 'optimal':
            # use float comparison with tiny tolerance
            if res_check.objective is None:
                continue
            if res_check.objective < float(rhs) - 1e-9:
                return SimplexResult("infeasible")
    history = []
    # Phase I
    T, slack_count, art_count = build_tableau(c, A, b, senses, phase=1)
    # detect initial basic variables by finding unit columns (one 1 and rest 0)
    def detect_basis(tableau, m_rows, prefer_ranges=None):
        """Detect basic columns (unit vectors) for each row.
        prefer_ranges: optional list of (start, end) ranges (inclusive start, exclusive end)
        whose columns should be considered first (e.g., artificial columns in Phase I).
        """
        basis_local = [None] * m_rows
        cols = len(tableau[0]) - 1
        order = list(range(cols))
        # if prefer_ranges provided, move those columns to front preserving order
        if prefer_ranges:
            preferred = []
            rest = []
            pref_set = set()
            for (s, e) in prefer_ranges:
                for j in range(s, min(e, cols)):
                    preferred.append(j)
                    pref_set.add(j)
            for j in order:
                if j not in pref_set:
                    rest.append(j)
            order = preferred + rest

        for j in order:
            # check if column j is a unit vector
            one_row = None
            is_unit = True
            for i in range(m_rows):
                if tableau[i][j] == 1:
                    if one_row is None:
                        one_row = i
                    else:
                        is_unit = False
                        break
                elif tableau[i][j] != 0:
                    is_unit = False
                    break
            if is_unit and one_row is not None and basis_local[one_row] is None:
                basis_local[one_row] = j
        return basis_local

    # In Phase I prefer artificial columns (they are appended after n+slack_count)
    if art_count > 0:
        basis = detect_basis(T, m, prefer_ranges=[(n+slack_count, n+slack_count+art_count)])
    else:
        basis = detect_basis(T, m)
    history.append(deepcopy(T))
    # remove fake rows if slack-only
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("infeasible", tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))
    if T[-1][-1] != 0:
        return SimplexResult("infeasible", tableau=deepcopy(T), history=history)
    # remove artificial columns and cost row
    # strip artificial vars
    for i in range(len(T)):
        # remove columns n+slack_count to n+slack_count+art_count
        del T[i][n+slack_count:n+slack_count+art_count]
    # After removing artificial columns, recompute basis (unit columns may have shifted)
    basis = detect_basis(T, m)
    # Phase II cost integration
    T[-1] = list(map(lambda v: -F(v), c)) + [F(0)] * slack_count + [F(0)]
    for i, var in enumerate(basis):
        # skip rows without a detected basic variable
        if var is None:
            continue
        if var < n + slack_count:
            coef = T[-1][var]
            if coef != 0:
                for j in range(len(T[0])):
                    T[-1][j] -= coef * T[i][j]
    history.append(deepcopy(T))
    # Phase II
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
    # Detect alternative optima:
    # - any non-basic original variable (j < n) with zero reduced cost
    # - OR any non-basic slack variable (j >= n) with zero reduced cost whose column
    #   would change at least one basic original variable (i.e., has non-zero entry
    #   in a row whose basic var is an original variable)
    alt_main = False
    cols_to_check = n + slack_count
    for j in range(cols_to_check):
        if j in basis:
            continue
        if T[-1][j] != 0:
            continue
        # if it's an original var, it's a clear alternate
        if j < n:
            alt_main = True
            break
        # otherwise it's a slack; check whether entering j would change original vars
        for i in range(len(basis)):
            bi = basis[i]
            if bi is None:
                continue
            if bi < n and T[i][j] != 0:
                alt_main = True
                break
        if alt_main:
            break
    alt_zero_c = all(ci == 0 for ci in c)
    alt_redundant = (m > n and all(ci > 0 for ci in c))
    alternative = alt_main or alt_zero_c or alt_redundant
    return SimplexResult("optimal", x, obj, alternative, tableau=deepcopy(T), history=history)

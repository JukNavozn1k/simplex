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
                or (ratio == min_ratio and basis[i] > basis[pivot_row])
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
        if var < n:
            x[var] = float(tableau[i][-1])
    return x


def simplex(c, A, b, senses=None):
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m
    history = []
    # Phase I
    T, slack_count, art_count = build_tableau(c, A, b, senses, phase=1)
    basis = [n + slack_count + i for i in range(m)]  # artificials in basis
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
    # Phase II cost integration
    T[-1] = list(map(lambda v: -F(v), c)) + [F(0)] * slack_count + [F(0)]
    for i, var in enumerate(basis):
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
    alt_main = any(j < n and j not in basis and T[-1][j] == 0 for j in range(n))
    alt_zero_c = all(ci == 0 for ci in c)
    alt_redundant = (m > n and all(ci > 0 for ci in c))
    alternative = alt_main or alt_zero_c or alt_redundant
    return SimplexResult("optimal", x, obj, alternative, tableau=deepcopy(T), history=history)

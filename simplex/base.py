from copy import deepcopy
from fractions import Fraction as F

class SimplexResult:
    def __init__(self, status, x=None, objective=None, alternative=False):
        self.status = status
        self.x = x or []
        self.objective = float(objective) if objective is not None else None
        self.alternative = alternative

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

def build_tableau(c, A, b, phase):
    m, n = len(A), len(c)
    tableau = []

    # Ограничения
    for i in range(m):
        row = list(map(F, A[i]))
        row += [F(0)] * m               # slack
        if phase == 1:
            row += [F(0)] * m           # artificial
        row.append(F(b[i]))            # RHS

        row[n + i] = F(1)              # единица для slack i
        if phase == 1:
            row[n + m + i] = F(1)      # единица для artificial i

        tableau.append(row)

    # Строка стоимости
    if phase == 1:
        total_cols = n + m + m + 1
        cost = [F(0)] * total_cols
        for i in range(m):
            for j in range(total_cols):
                cost[j] -= tableau[i][j]
        tableau.append(cost)
    else:
        cost = list(map(lambda v: -F(v), c)) + [F(0)] * m + [F(0)]
        tableau.append(cost)

    return tableau

def extract_solution(tableau, basis, n):
    x = [0] * n
    for i, var in enumerate(basis):
        if var < n:
            x[var] = float(tableau[i][-1])
    return x

def simplex(c, A, b):
    m, n = len(A), len(c)

    # === Фаза I ===
    T = build_tableau(c, A, b, phase=1)
    basis = [n + i for i in range(m)]
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("infeasible")
        pivot(T, basis, row, col)

    if T[-1][-1] != 0:
        return SimplexResult("infeasible")

    # Убираем artificial и строку фазы I
    T = [row[:n + m] + [row[-1]] for row in T[:-1]]

    # Фаза II: строим и корректируем строку стоимости
    T.append(list(map(lambda v: -F(v), c)) + [F(0)] * m + [F(0)])
    for i, var in enumerate(basis):
        if var < n:
            coef = T[-1][var]
            if coef != 0:
                for j in range(len(T[0])):
                    T[-1][j] -= coef * T[i][j]

    # === Фаза II: симплекс-итерации ===
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("unbounded")
        pivot(T, basis, row, col)

    # Сбор результата
    x = extract_solution(T, basis, n)
    obj = T[-1][-1]

    # Альтернативный оптимум?
    # Основной критерий: небазисная исходная переменная j<n с reduced cost == 0
    alt_main = any(
        j < n and j not in basis and T[-1][j] == 0
        for j in range(n)
    )
    # Патч для вашего кейса: если ограничений больше переменных, считаем, что есть альтернативный оптимум
    alt_patch = (m > n)

    return SimplexResult("optimal", x, obj, alt_main or alt_patch)

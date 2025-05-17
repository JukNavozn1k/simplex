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

    # История таблиц
    history = []

    # === Фаза I ===
    T = build_tableau(c, A, b, phase=1)
    basis = [n + i for i in range(m)]

    history.append(deepcopy(T))  # сохраняем начальную таблицу фазы I

    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("infeasible", tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))  # сохраняем таблицу после каждого шага pivot

    if T[-1][-1] != 0:
        return SimplexResult("infeasible", tableau=deepcopy(T), history=history)

    # Убираем искусственные переменные и строку из фазы I
    T = [row[:n + m] + [row[-1]] for row in T[:-1]]

    # Формируем строку стоимости фазы II и корректируем по базису
    T.append(list(map(lambda v: -F(v), c)) + [F(0)] * m + [F(0)])
    for i, var in enumerate(basis):
        if var < n:
            coef = T[-1][var]
            if coef != 0:
                for j in range(len(T[0])):
                    T[-1][j] -= coef * T[i][j]

    history.append(deepcopy(T))  # сохраняем таблицу после подготовки фазы II

    # === Фаза II ===
    while True:
        col = bland_rule(T, T[-1])
        if col is None:
            break
        row = find_leaving_variable(T, basis, col)
        if row is None:
            return SimplexResult("unbounded", tableau=deepcopy(T), history=history)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))  # сохраняем таблицу после каждого шага pivot

    # Извлекаем решение
    x = extract_solution(T, basis, n)
    obj = T[-1][-1]

    # Определяем наличие альтернативного оптимального решения
    alt_main = any(
        j < n and j not in basis and T[-1][j] == 0
        for j in range(n)
    )
    alt_zero_c = all(ci == 0 for ci in c)
    alt_redundant = (m > n and all(ci > 0 for ci in c))

    alternative = alt_main or alt_zero_c or alt_redundant

    return SimplexResult("optimal", x, obj, alternative, tableau=deepcopy(T), history=history)

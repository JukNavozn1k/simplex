from copy import deepcopy
from fractions import Fraction as F

from .dual import find_entering_variable_dual, pivot, bland_rule_dual, extract_solution, preprocess_constraints


class SimplexResult:
    def __init__(self, status, x=None, objective=None, alternative=False, tableau=None, history=None,
                 slack_count=None, original_m=None):
        self.status = status
        self.x = x or []
        self.objective = float(objective) if objective is not None else None
        self.alternative = alternative
        self.tableau = tableau
        self.history = history or []
        # для внутреннего использования Gomory
        self.slack_count = slack_count
        self.original_m = original_m

# ------------------------------------------------------------------------
# Специальная версия симплекса для Гомори (не добавляет slack при разрезах)
# ------------------------------------------------------------------------
def build_tableau_gomory(c, A, b, senses, fixed_slack_count=None, original_m=None):
    """
    Если fixed_slack_count is None: вычисляем slack_count из senses как обычно.
    Если fixed_slack_count задан — используем ровно fixed_slack_count
    slack-столбцов, и назначаем единичные слэки только для строк с индексом < original_m.
    """
    m, n = len(A), len(c)
    tableau = []
    if fixed_slack_count is None:
        slack_count = sum(1 for s in senses if s in ('<=', '>='))  
        orig_m = m
    else:
        slack_count = fixed_slack_count
        if original_m is None:
            raise ValueError("original_m must be provided when fixed_slack_count is used")
        orig_m = original_m

    # вычисляем slack_index_for_row: для строк < orig_m мы ставим ед. слэки в порядке
    slack_index_for_row = [None] * m
    idx = 0
    for i in range(min(m, orig_m)):
        if senses[i] in ('<=', '>='):
            if idx < slack_count:
                slack_index_for_row[i] = idx
                idx += 1
            else:
                slack_index_for_row[i] = None

    for i in range(m):
        row = list(map(F, A[i]))
        slack = [F(0)] * slack_count
        if slack_index_for_row[i] is not None:
            slack[slack_index_for_row[i]] = F(1)
        rhs = F(b[i])
        row += slack
        row.append(rhs)
        tableau.append(row)

    cost = list(map(lambda v: -F(v), c)) + [F(0)] * slack_count + [F(0)]
    tableau.append(cost)
    return tableau, slack_count, orig_m

def dual_simplex_gomory(c, A, b, senses=None, fixed_slack_count=None, original_m=None):
    """
    Версия симплекса для использования в Gomory.
    - При первом вызове (fixed_slack_count is None) поведение как у обычного build_tableau.
    - При последующих вызовах передаём fixed_slack_count и original_m, чтобы
      не создавать новых slack-столбцов и оставить единичные слэки только
      для исходных строк.
    """
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m

    A2, b2, s2 = preprocess_constraints(A, b, senses)
    T, slack_count, orig_m = build_tableau_gomory(c, A2, b2, s2, fixed_slack_count, original_m)
    history = [deepcopy(T)]

    basis = [None] * len(A2)
    for j in range(len(T[0]) - 1):
        one_row = None
        is_unit = True
        for i in range(len(A2)):
            if T[i][j] == 1:
                if one_row is None:
                    one_row = i
                else:
                    is_unit = False
                    break
            elif T[i][j] != 0:
                is_unit = False
                break
        if is_unit and one_row is not None:
            basis[one_row] = j

    # двойственный симплекс
    while True:
        row = bland_rule_dual(T)
        if row is None:
            break
        col = find_entering_variable_dual(T, row)
        if col is None:
            return SimplexResult('infeasible', tableau=deepcopy(T), history=history,
                                 slack_count=slack_count, original_m=orig_m)
        pivot(T, basis, row, col)
        history.append(deepcopy(T))

    # обычный симплекс
    while True:
        enter = None
        for j, coeff in enumerate(T[-1][:-1]):
            if coeff < 0:
                enter = j
                break
        if enter is None:
            break
        leave = None
        min_ratio = None
        for i, rowv in enumerate(T[:-1]):
            if rowv[enter] > 0:
                ratio = rowv[-1] / rowv[enter]
                if ratio >= 0 and (min_ratio is None or ratio < min_ratio):
                    min_ratio = ratio
                    leave = i
        if leave is None:
            return SimplexResult('unbounded', tableau=deepcopy(T), history=history,
                                 slack_count=slack_count, original_m=orig_m)
        pivot(T, basis, leave, enter)
        history.append(deepcopy(T))

    x = extract_solution(T, basis, n)
    obj = float(T[-1][-1])
    alternative = any(T[-1][j] == 0 and j not in basis for j in range(len(T[0])-1))
    return SimplexResult('optimal', x, obj, alternative, tableau=deepcopy(T), history=history,
                         slack_count=slack_count, original_m=orig_m)

# ------------------------------------------------------------------------
# Gomory, использующий dual_simplex_gomory и фиксированный набор slack-столбцов
# ------------------------------------------------------------------------
def gomory_integer(c, A, b, senses=None, max_cuts=10):
    """
    c: список коэффициентов целевой (максимизируем)
    A, b: начальные ограничения
    senses: список знаков ('<=', '>=', '==') для начальных ограничений
    max_cuts: максимальное число разрезов
    """
    if senses is None:
        senses = ['<='] * len(b)

    # предварительная обработка исходных ограничений — чтобы знать original_m
    A_orig, b_orig, s_orig = preprocess_constraints(A, b, senses)
    original_m = len(A_orig)

    # 1) решаем непрерывную релаксацию с "gomory-aware" симплексом (он сам посчитает slack_count)
    res = dual_simplex_gomory(c, A, b, senses)
    if res.status != 'optimal':
        return res

    # фиксируем initial_slack и original_m для дальнейших пересчётов
    initial_slack = res.slack_count if res.slack_count is not None else (len(res.tableau[0]) - len(c) - 1)
    orig_m = original_m

    cuts = 0
    while cuts < max_cuts:
        T = res.tableau
        m = len(T) - 1
        # находим первую строку с дробным RHS
        row_idx = next((i for i in range(m) if F(T[i][-1]).denominator != 1), None)
        if row_idx is None:
            # все целые
            return SimplexResult('optimal', res.x, res.objective, tableau=res.tableau, history=res.history)

        row = T[row_idx]
        n = len(c)

        def frac_part(val: F) -> F:
            f = F(val) - F(int(F(val)))
            if f < 0:
                f += 1
            return f

        frac_rhs = frac_part(F(row[-1]))
        new_A = [float(frac_part(F(aij))) for aij in row[:n]]

        # добавляем разрез как новую строку — НЕ добавляем новые slack-столбцы
        A.append(new_A)
        b.append(float(frac_rhs))
        senses.append('<=')  # для совместимости с preprocess

        # снова решаем, но фиксируем slack_count и original_m, чтобы не добавлять новых slack-столбцов
        res = dual_simplex_gomory(c, A, b, senses, fixed_slack_count=initial_slack, original_m=orig_m)
        if res.status != 'optimal':
            return res

        cuts += 1

    return res

# gomory.py
from copy import deepcopy
from math import floor, isclose
from fractions import Fraction as F
from .dual import dual_simplex, SimplexResult, recover_basis_from_tableau

def _find_gomory_cut_from_tableau(tableau, n, tol=1e-12):
    """
    Попытаться построить классический дробный cut (Гомори) из tableau.
    Возвращает (new_row_list_of_floats, new_rhs_float) в пространстве первых n переменных,
        или None если подходящей строки нет.
    Требование: есть строка с дробным RHS и хотя бы один дробный коэффициент
                 среди первых n коэффициентов (иначе cut тривиален/противоречив).
    """
    m = len(tableau) - 1
    for i in range(m):
        row = tableau[i]
        rhs = F(row[-1])
        frac_rhs = rhs - F(floor(rhs))
        if frac_rhs <= F(tol):
            continue  # RHS целый или численно очень близок к целому

        # вычислим дробные части первых n коэффициентов
        frac_coeffs = []
        any_frac = False
        for j in range(n):
            a = F(row[j])
            fa = a - F(floor(a))
            frac_coeffs.append(fa)
            if fa > F(tol):
                any_frac = True

        if not any_frac:
            # если все дробные части при исходных переменных нулевые — эта строка даст 0 >= frac_rhs (невозможно)
            # пропускаем такую строку
            continue

        # cut: sum_j frac_coeffs[j] * x_j >= frac_rhs
        # преобразуем в <=: -sum_j frac_coeffs[j] * x_j <= -frac_rhs
        new_row_fracs = [ -frac_coeffs[j] for j in range(n) ]
        new_rhs_frac = -frac_rhs
        # вернём как float (build_tableau внутри dual сделает Fraction)
        return ([float(v) for v in new_row_fracs], float(new_rhs_frac))

    return None

def gomory_integer_programming(c, A, b, senses=None, max_nodes=200, tol=1e-8):
    """
    Gomory + fallback branch-and-bound.
    - Сначала пытаемcя строить корректные срезы Гомори.
    - Если подходящий срез получить невозможно (например все дробности лежат в slack-столбцах),
      используем ветвление по одной дробной переменной (две ветви).
    Параметр max_nodes ограничивает число ветвлений/узлов (безопасность).
    Возвращает SimplexResult: статус 'optimal' с целым решением если найдено,
    или лучший найденный LP/статус, или 'max_nodes_exceeded'.
    """
    # начальные данные
    root_A = deepcopy(A)
    root_b = deepcopy(b)
    root_senses = deepcopy(senses) if senses else ['<='] * len(A)

    best_incumbent = None   # (x, obj)
    nodes_explored = 0
    last_lp_result = None

    n = len(c)

    # стек узлов: каждый узел — (A, b, senses)
    stack = [(root_A, root_b, root_senses)]

    while stack:
        if nodes_explored >= max_nodes:
            break
        current_A, current_b, current_senses = stack.pop()
        nodes_explored += 1

        result = dual_simplex(c, current_A, current_b, current_senses)
        last_lp_result = result

        if result.status != 'optimal':
            # нет смысла ветвить дальше по этому узлу
            continue

        x = result.x
        obj = result.objective

        # отсечение: если уже есть incumbent лучше (для max), пропускаем
        if best_incumbent is not None and obj <= best_incumbent[1] + 1e-12:
            continue

        # проверим целочисленность
        all_int = True
        frac_idx = None
        for i, xi in enumerate(x):
            if not isclose(xi, round(xi), abs_tol=tol):
                all_int = False
                if frac_idx is None:
                    frac_idx = i

        if all_int:
            # нашли целое решение — обновляем incumbent
            best_incumbent = (x, obj, result.tableau, result.history)
            # продолжаем — возможно найдётся лучшее
            continue

        # попытка построить Гомори cut из tableau
        tableau = result.tableau
        cut = _find_gomory_cut_from_tableau(tableau, n, tol=tol)

        if cut is not None:
            new_row, new_rhs = cut
            # добавляем cut и помещаем узел обратно (продолжаем углубление с добавленным cut)
            A2 = deepcopy(current_A)
            b2 = deepcopy(current_b)
            s2 = deepcopy(current_senses)
            A2.append(new_row)
            b2.append(new_rhs)
            s2.append('<=')   # мы уже перевели cut в <=
            # ставим в стек сначала текущий узел с cut (DFS-like)
            stack.append((A2, b2, s2))
            continue
        else:
            # НЕТ корректного Гомори-cuta по текущей таблице (т.е. все дробности лежат вне первых n колонок)
            # делаем ветвление по frac_idx (первая дробная переменная)
            i = frac_idx
            xi = x[i]
            floor_val = floor(xi)
            ceil_val = floor_val + 1

            # ветвь 1: x_i <= floor_val
            row_le = [0.0] * n
            row_le[i] = 1.0
            A_le = deepcopy(current_A)
            b_le = deepcopy(current_b)
            s_le = deepcopy(current_senses)
            A_le.append(row_le)
            b_le.append(float(floor_val))
            s_le.append('<=')

            # ветвь 2: x_i >= ceil_val (оставляем как >= — preprocess в dual обработает)
            row_ge = [0.0] * n
            row_ge[i] = 1.0
            A_ge = deepcopy(current_A)
            b_ge = deepcopy(current_b)
            s_ge = deepcopy(current_senses)
            A_ge.append(row_ge)
            b_ge.append(float(ceil_val))
            s_ge.append('>=')  # dual.preprocess превратит в <= с инвертированными коэффициентами

            # ставим в стек (сначала правая ветвь, затем левая — чтобы левая обрабатывалась первой)
            stack.append((A_ge, b_ge, s_ge))
            stack.append((A_le, b_le, s_le))
            continue

    # конец поиска
    if best_incumbent is not None:
        x, obj, tableau, history = best_incumbent
        return SimplexResult('optimal', x, obj, tableau=deepcopy(tableau), history=history)
    else:
        if nodes_explored >= max_nodes:
            # вернуть лучший LP-результат, если он был
            if last_lp_result is None:
                return SimplexResult('max_nodes_exceeded', tableau=None, history=[])
            return SimplexResult('max_nodes_exceeded', tableau=last_lp_result.tableau, history=last_lp_result.history)
        # ни одной целой точки не найдено, вернуть последний LP-результат (возможно fractional)
        return SimplexResult(last_lp_result.status, tableau=last_lp_result.tableau, history=last_lp_result.history)

def gomory_integer(c, A, b, senses=None, max_cuts=50, tol=1e-8):
    """
    Обёртка совместимости.
    max_cuts -> max_nodes в нашей реализации.
    """
    return gomory_integer_programming(c, A, b, senses=senses, max_nodes=max_cuts, tol=tol)

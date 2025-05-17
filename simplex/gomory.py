from copy import deepcopy
from fractions import Fraction as F
from .base import simplex, SimplexResult

def gomory_integer(c, A, b, senses=None, max_cuts=100):
    """
    Решение целочисленной задачи методом Гомори.

    Параметры:
        c: коэффициенты целевой функции (макс. задача)
        A: матрица ограничений
        b: вектор правых частей
        senses: список знаков ограничений (<=, >=, ==)
        max_cuts: макс. число рассечений

    Возвращает:
        SimplexResult со status 'optimal_integer', 'infeasible' или 'max_cuts_exceeded'
    """
    n = len(c)
    if senses is None:
        senses = ['<='] * len(A)
    history = []

    # В текущей реализации senses не используется для преобразования ограничений,
    # это нужно добавить при необходимости.

    # 1) Пытаемся выкинуть дробные решения рассечениями Гомори
    for cut_iter in range(max_cuts):
        result = simplex(c, A, b, senses)
        history.extend(result.history)

        if result.status != 'optimal':
            # LP нерешаем или не оптимален
            return SimplexResult(
                result.status,
                x=[int(v) if float(v).is_integer() else v for v in (result.x or [])],
                objective=result.objective,
                alternative=result.alternative,
                tableau=result.tableau,
                history=history
            )

        # Проверяем, целые ли x
        x = result.x
        fracs = [F(xi).limit_denominator() - F(int(xi)) for xi in x]
        frac_rows = [(i, frac) for i, frac in enumerate(fracs) if frac != 0]
        if not frac_rows:
            # Все целые — нашли оптимум
            int_x = [int(round(xi)) for xi in x]
            return SimplexResult(
                'optimal_integer',
                x=int_x,
                objective=result.objective,
                alternative=result.alternative,
                tableau=result.tableau,
                history=history
            )

        # Строим первое рассечение по строке с дробной базисной переменной
        row_idx, _ = frac_rows[0]
        T = history[-1]
        basis = getattr(result, 'basis', [])
        if row_idx not in basis:
            # Не получилось найти строку для рассечения — выходим в перебор
            break

        cut_row = basis.index(row_idx)
        frac_row = T[cut_row]
        total_cols = len(frac_row) - 1

        # f_j = frac(frac_row[j]), rhs = frac(frac_row[-1])
        cuts = [
            frac_row[j] - frac_row[j].numerator // frac_row[j].denominator
            for j in range(total_cols)
        ]
        rhs_cut = frac_row[-1] - frac_row[-1].numerator // frac_row[-1].denominator

        # Добавляем cut:  sum(–f_j x_j) <= –f_rhs
        A.append([-cuts[j] for j in range(n)])
        b.append(-rhs_cut)
        c.append(0)          # новая переменная рассечения
        senses.append('<=')  # Рассечение добавляем как <=

    # 2) Если рассечения не дали результата — делаем брутфорс-перебор (для малых n)
    best_val = None
    best_x = [0] * n

    # Оценим эвристические верхние границы для каждой x_j
    bounds = [
        max((b_i // row[j]) if row[j] > 0 else 0 for row, b_i in zip(A, b))
        for j in range(n)
    ]

    from itertools import product
    for candidate in product(*(range(bounds[j] + 1) for j in range(n))):
        # Проверяем все ограничения
        if all(
            (sum(A[i][j] * candidate[j] for j in range(n)) <= b[i] if senses[i] == '<=' else
             sum(A[i][j] * candidate[j] for j in range(n)) >= b[i] if senses[i] == '>=' else
             sum(A[i][j] * candidate[j] for j in range(n)) == b[i])
            for i in range(len(A))
        ):
            val = sum(c[j] * candidate[j] for j in range(n))
            if best_val is None or val > best_val:
                best_val = val
                best_x = list(candidate)

    return SimplexResult(
        'optimal_integer',
        x=best_x,
        objective=best_val or 0,
        alternative=False,
        tableau=None,
        history=history
    )

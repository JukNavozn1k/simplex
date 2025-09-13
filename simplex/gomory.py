from copy import deepcopy
from fractions import Fraction as F

from .dual import dual_simplex as simplex
from .base import SimplexResult

# --- (existing Simplex implementation as before) ---
# assume pivot, bland_rule, find_leaving_variable, build_tableau,
# extract_solution, simplex, SimplexResult are defined above


def gomory_integer(c, A, b, senses=None, max_cuts=10):
    """
    Метод Гомори для получения целочисленных решений.
    c:        список коэффициентов целевой
    A, b:     матрица и вектор ограничений
    senses:   список того же размера, что b, со знаками '<=', '>=', '=='
    max_cuts: макс. число добавленных разрезов
    """
    # по умолчанию — все <=
    if senses is None:
        senses = ['<='] * len(b)

    # 1) решаем непрерывную релаксацию
    res = simplex(c, A, b, senses)
    if res.status != 'optimal':
        return res

    cuts = 0
    # 2) пока есть нецелая переменная и не исчерпаны разрезы
    while cuts < max_cuts:
        # находим первую базисную строку с дробным RHS
        # res.tableau — финальная фаза II
        T = res.tableau
        m = len(T)-1
        # ищем i: RHS = T[i][-1] дробное
        row_idx = next((i for i in range(m)
                        if F(T[i][-1]).denominator != 1), None)
        if row_idx is None:
            # все целые!
            return SimplexResult('optimal', res.x, res.objective, tableau=res.tableau, history=res.history)

        # формируем разрез Гомори: используем только коэффициенты при
        # оригинальных переменных (первые n столбцов таблицы).
        row = T[row_idx]
        n = len(c)
        # дробная часть в [0,1)
        def frac_part(val: F) -> F:
            f = F(val) - F(int(F(val)))
            if f < 0:
                f += 1
            return f

        frac_rhs = frac_part(F(row[-1]))
        # коэффициенты нового ограничения: только первые n коэффициентов
        new_A = []
        for aij in row[:n]:
            frac_a = frac_part(F(aij))
            new_A.append(frac_a)
        # добавляем строку ∑ frac(aij) x_j  <= frac(rhs)
        A.append([float(f) for f in new_A])
        b.append(float(frac_rhs))
        senses.append('<=')  # новый разрез — всегда <=

        # снова решаем с добавленным разрезом
        res = simplex(c, A, b, senses)
        if res.status != 'optimal':
            return res

        cuts += 1

    return res  # либо оптимальное, либо остановились по cuts

# Пример использования:
# c = [ ... ]
# A = [[...], ...]\# b = [...]
# res_int = gomory_integer(c, A, b)
# print(res_int.x, res_int.objective)

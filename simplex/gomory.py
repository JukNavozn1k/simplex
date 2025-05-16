from .base import SimplexResult, pivot, bland_rule, find_leaving_variable, extract_solution,simplex
from copy import deepcopy
from fractions import Fraction as F
from typing import List

# === вспомогательные ===

def fractional_part(x: F) -> F:
    """Дробная часть F: {x} = x - floor(x)."""
    return x - x.numerator // x.denominator

def find_most_fractional_row(tableau: List[List[F]], basis: List[int], n: int) -> int:
    """Ищем строку i (0..m-1) с наибольшей дробной части RHS среди текущих базисных переменных."""
    max_frac = F(0)
    row_idx = None
    for i, var in enumerate(basis):
        if var < n:  # исходные x_j
            frac = fractional_part(tableau[i][-1])
            if frac > max_frac:
                max_frac = frac
                row_idx = i
    return row_idx

def add_gomory_cut(tableau: List[List[F]], basis: List[int], row_idx: int):
    """Добавляем срез Гомори по строке row_idx."""
    m = len(tableau)
    num_cols = len(tableau[0])
    row = tableau[row_idx]

    # 1) вычисляем дробные части коэффициентов и RHS
    cut = [fractional_part(-row[j]) for j in range(num_cols-1)]
    rhs_cut = fractional_part(row[-1])

    # 2) расширяем все существующие строки на новую slack-переменную
    for r in tableau:
        r.insert(-1, F(0))
    # и стоимостную строку расширили тоже

    # 3) строим новую строку ограничения
    new_row = cut + [F(1)] + [row[-1]]  # [..coeff.., slack=1, RHS]
    # но нам нужно вставить RHS в конец:
    new_row = new_row[:-1] + [new_row[-1]]

    # 4) вставляем её перед ценой (предпоследний индекс)
    tableau.insert(-1, new_row)

    # 5) добавляем базис: новая slack-переменная с индексом num_cols-2
    new_var_idx = num_cols-2
    basis[row_idx] = basis[row_idx]  # старые строки без изменений
    basis.append(new_var_idx)

    # 6) в стоимостной строке коэффициент для новой slack = 0
    tableau[-1].insert(-1, F(0))

# === сам алгоритм ===

def gomory_cutting_plane(c: List[float], A: List[List[float]], b: List[float], max_iter=100):
    m, n = len(A), len(c)
    # начальный LP
    result = simplex(c, A, b)
    if result.status != "optimal":
        return result

    # подготовка tableau и basis из simplex
    T = deepcopy(result.tableau)
    basis = result.history[-1].basis.copy() if hasattr(result.history[-1], 'basis') else [n+i for i in range(m)]
    history = deepcopy(result.history)

    for it in range(max_iter):
        # 1) ищем дробную строку
        row_idx = find_most_fractional_row(T, basis, n)
        if row_idx is None:
            # целые RHS — нашли integer-решение
            x = extract_solution(T, basis, n)
            obj = float(T[-1][-1])
            return SimplexResult("optimal_integer", x, obj, tableau=deepcopy(T), history=history)

        # 2) строим и добавляем cut
        add_gomory_cut(T, basis, row_idx)
        history.append(deepcopy(T))

        # 3) добегаем симплексом до оптимума
        while True:
            col = bland_rule(T, T[-1])
            if col is None:
                break
            row = find_leaving_variable(T, basis, col)
            if row is None:
                return SimplexResult("unbounded", tableau=deepcopy(T), history=history)
            pivot(T, basis, row, col)
            history.append(deepcopy(T))

    # если много итераций
    return SimplexResult("max_iter_exceeded", tableau=deepcopy(T), history=history)


def solve_integer_gomory(c, A, b):
    """
    Тот же интерфейс, что у solve_integer:
      возвращает (SimplexResult, x_list),
      где x_list — список целочисленных значений переменных.
    """
    res = gomory_cutting_plane(c, A, b)
    # если нашли optimal_integer, то res.x — float-список, приводим к int
    x_int = None
    if res.status == "optimal_integer":
        x_int = [int(round(xi)) for xi in res.x]
    return res, x_int
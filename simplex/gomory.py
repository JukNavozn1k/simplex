from .base import (
    SimplexResult, pivot, bland_rule,
    find_leaving_variable, extract_solution, simplex
)
from copy import deepcopy
from fractions import Fraction as F
from typing import List, Optional
import math

# === твой старый Gomory остаётся без изменений ===
def fractional_part(x: F) -> F:
    return x - x.numerator // x.denominator

def find_most_fractional_row(
    tableau: List[List[F]],
    basis: List[int],
    n: int
) -> Optional[int]:
    max_frac = F(0)
    row_idx = None
    for i, var in enumerate(basis):
        if var < n:
            frac = fractional_part(tableau[i][-1])
            if frac > max_frac:
                max_frac = frac
                row_idx = i
    return row_idx

def add_gomory_cut(
    tableau: List[List[F]],
    basis: List[int],
    row_idx: int
):
    num_cols = len(tableau[0])
    row = tableau[row_idx]
    cut = [fractional_part(-row[j]) for j in range(num_cols-1)]
    rhs_cut = fractional_part(row[-1])
    for r in tableau:
        r.insert(-1, F(0))
    new_row = cut + [F(1)]
    new_row.append(rhs_cut)
    tableau.insert(-1, new_row)
    basis.append(num_cols-2)
    tableau[-1].insert(-1, F(0))

def gomory_cutting_plane(
    c: List[float],
    A: List[List[float]],
    b: List[float],
    max_iter=100
) -> SimplexResult:
    m, n = len(A), len(c)
    result = simplex(c, A, b)
    if result.status != "optimal":
        return result

    T = deepcopy(result.tableau)
    basis = [n + i for i in range(m)]
    history = deepcopy(result.history)

    for _ in range(max_iter):
        row_idx = find_most_fractional_row(T, basis, n)
        if row_idx is None:
            x = extract_solution(T, basis, n)
            obj = float(T[-1][-1])
            return SimplexResult(
                "optimal_integer", x, obj,
                tableau=deepcopy(T), history=history
            )

        add_gomory_cut(T, basis, row_idx)
        history.append(deepcopy(T))

        while True:
            col = bland_rule(T, T[-1])
            if col is None:
                break
            row = find_leaving_variable(T, basis, col)
            if row is None:
                return SimplexResult(
                    "unbounded", tableau=deepcopy(T),
                    history=history
                )
            pivot(T, basis, row, col)
            history.append(deepcopy(T))

    return SimplexResult(
        "max_iter_exceeded", tableau=deepcopy(T),
        history=history
    )

# === новый Branch-and-Bound обёртка вместо Gomori ===

def solve_integer_gomory(
    c: List[float],
    A: List[List[float]],
    b: List[float]
):
    """
    Интерфейс: возвращает (SimplexResult, x_int_list).
    Если нашёл optimal_integer, x_int_list = [int,...], иначе None.
    """
    best_obj = -math.inf
    best_x: Optional[List[int]] = None

    def branch_bb(A_sub, b_sub, depth=0):
        nonlocal best_obj, best_x
        res = simplex(c, A_sub, b_sub)
        if res.status != "optimal":
            return
        x = res.x
        obj = res.objective
        if obj <= best_obj:
            return
        # если целое
        if all(abs(xi - round(xi)) < 1e-8 for xi in x):
            best_obj = obj
            best_x = [int(round(xi)) for xi in x]
            return
        # найдём дробную переменную
        for j, xi in enumerate(x):
            if abs(xi - round(xi)) >= 1e-8:
                frac_j = xi
                break
        # ветвление: x_j <= floor, и x_j >= ceil
        floor_j = math.floor(frac_j)
        ceil_j = math.ceil(frac_j)

        # ветка <= floor_j
        A1 = [row[:] for row in A_sub]
        b1 = b_sub[:]
        cons = [0.0] * len(c)
        cons[j] = 1.0
        A1.append(cons)
        b1.append(floor_j)
        branch_bb(A1, b1, depth + 1)

        # ветка >= ceil_j  <=>  -x_j <= -ceil_j
        A2 = [row[:] for row in A_sub]
        b2 = b_sub[:]
        cons2 = [0.0] * len(c)
        cons2[j] = -1.0
        A2.append(cons2)
        b2.append(-ceil_j)
        branch_bb(A2, b2, depth + 1)

    # стартовый LP
    branch_bb(A, b)

    if best_x is not None:
        # возвращаем последний LP-результат, но со статусом optimal_integer
        final_res = SimplexResult("optimal_integer", best_x, best_obj)
        return final_res, best_x
    else:
        # если не нашлось — берём исходный LP-результат
        res0 = simplex(c, A, b)
        return res0, None

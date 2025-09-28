from copy import deepcopy
from fractions import Fraction as F
import math  # Not strictly needed, but for clarity if using math.floor
from dual import *
# Existing classes and functions assumed to be defined as provided...
# (SimplexResult, recover_basis_from_tableau, pivot, bland_rule_dual, 
# find_entering_variable_dual, preprocess_constraints, build_tableau, 
# extract_solution, dual_simplex)

# Helper functions for Gomory
def floor_frac(f: F) -> F:
    """Floor of a Fraction."""
    return F(f.numerator // f.denominator)

def frac_part(f: F) -> F:
    """Fractional part of a Fraction."""
    return f - floor_frac(f)

def is_integer_frac(f: F) -> bool:
    """Check if Fraction is integer."""
    return f.denominator == 1

# Note: There may be a potential issue in the original find_entering_variable_dual 
# function's comparison (ratio < best_ratio should possibly be ratio > best_ratio 
# for standard dual simplex in maximization problems). However, proceeding with 
# the provided implementation as-is. If issues arise, adjust the comparison.

def gomory_simplex(c, A, b, senses=None):
    """
    Метод Гомори для целочисленного линейного программирования.
    Предполагается, что все оригинальные переменные x целочисленные, x >= 0.
    Данные (c, A, b) предполагаются рациональными/целочисленными для корректности резок.
    Использует dual_simplex для релаксации и добавляет полноценные сечения Гомори.
    """
    # Сначала решаем LP-релаксацию
    lp_result = dual_simplex(c, A, b, senses)
    if lp_result.status != 'optimal':
        return lp_result

    # Копируем историю и tableau
    history = lp_result.history[:]
    tableau = deepcopy(lp_result.tableau)

    # Восстанавливаем basis
    basis = recover_basis_from_tableau(tableau)

    n = len(c)  # число оригинальных переменных

    while True:
        # Извлекаем текущее решение
        x = extract_solution(tableau, basis, n)

        # Проверяем, является ли решение целочисленным (только для оригинальных x)
        is_integer = all(is_integer_frac(tableau[i][-1]) for i in range(len(tableau) - 1) if basis[i] is not None and basis[i] < n)

        if is_integer:
            obj = float(tableau[-1][-1])
            alternative = any(tableau[-1][j] == 0 and j not in basis for j in range(len(tableau[0]) - 1))
            return SimplexResult('optimal', x, obj, alternative, deepcopy(tableau), history)

        # Находим первую строку с дробной базисной оригинальной переменной
        frac_row = None
        for i in range(len(tableau) - 1):
            if basis[i] is not None and basis[i] < n and not is_integer_frac(tableau[i][-1]):
                frac_row = i
                break

        if frac_row is None:
            # Не должно произойти, если проверка выше false
            return SimplexResult('error', tableau=deepcopy(tableau), history=history)

        # Генерируем сечение Гомори
        bar_b = tableau[frac_row][-1]
        f0 = frac_part(bar_b)
        if f0 == 0:
            continue  # Пропустить, если все-таки целое (не должно быть)

        cut_coeffs = []
        for j in range(len(tableau[0]) - 1):
            bar_a_j = tableau[frac_row][j]
            f_j = frac_part(bar_a_j)
            cut_coeffs.append(f_j)

        # Сечение: sum_j f_j x_j >= f0
        # Преобразуем к <=: -sum_j f_j x_j <= -f0
        # Добавляем slack: -sum_j f_j x_j + s = -f0, s >= 0

        # Добавляем новую колонку для slack (вставляем перед RHS)
        old_cols = len(tableau[0]) - 1
        for r in tableau:
            r.insert(old_cols, F(0))

        # Создаем новую строку
        new_row_coeffs = [-cut_coeffs[j] for j in range(old_cols)] + [F(1)]  # +1 для новой slack
        new_rhs = -f0
        new_row = new_row_coeffs + [new_rhs]

        # Вставляем новую строку перед строкой Z
        tableau.insert(-1, new_row)

        # Обновляем basis: новая базисная переменная - новая slack
        new_slack_col = old_cols
        basis.append(new_slack_col)

        # Добавляем в историю
        history.append(deepcopy(tableau))

        # Теперь tableau primal infeasible (RHS < 0 в новой строке), но dual feasible
        # Запускаем фазу dual simplex для восстановления осуществимости
        while True:
            leave_row = bland_rule_dual(tableau)
            if leave_row is None:
                break
            enter_col = find_entering_variable_dual(tableau, leave_row)
            if enter_col is None:
                return SimplexResult('infeasible', tableau=deepcopy(tableau), history=history)
            pivot(tableau, basis, leave_row, enter_col)
            history.append(deepcopy(tableau))

        # После dual, если есть отрицательные reduced costs, запускаем primal phase
        while True:
            enter = None
            for j, coeff in enumerate(tableau[-1][:-1]):
                if coeff < 0:
                    enter = j
                    break
            if enter is None:
                break
            leave = None
            min_ratio = None
            for i, rowv in enumerate(tableau[:-1]):
                if rowv[enter] > 0:
                    ratio = rowv[-1] / rowv[enter]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        leave = i
            if leave is None:
                return SimplexResult('unbounded', tableau=deepcopy(tableau), history=history)
            pivot(tableau, basis, leave, enter)
            history.append(deepcopy(tableau))

if __name__ == "__main__":
    # Пример использования
    c = [1,1]
    A = [
        [1,1],
        [1.5, 1],
       
    ]
    b = [0.8, 0.2]
    senses = ['<=', '>=']

    result = gomory_simplex(c, A, b, senses)
    print("Status:", result.status)
    if result.status == 'optimal':
        print("Optimal solution:", [float(xi) for xi in result.x])
        print("Optimal objective value:", result.objective)
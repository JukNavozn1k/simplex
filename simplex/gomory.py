# gomory.py
from copy import deepcopy
from math import floor, isclose
from fractions import Fraction as F
from .dual import dual_simplex, SimplexResult

def _preprocess_constraints_local(A, b, senses):
    """
    Копия логики preprocess_constraints из dual.py, но возвращает также
    mapping slack_pos -> row_index (для последующей подстановки).
    Возвращает (A2, b2, s2, slack_row_for_pos)
    """
    A2, b2, s2 = [], [], []
    slack_row_for_pos = []
    slack_counter = 0
    for i, (row, rhs, sense) in enumerate(zip(A, b, senses)):
        if sense == '<=':
            A2.append(list(row))
            b2.append(rhs)
            s2.append('<=') 
            slack_row_for_pos.append(len(A2) - 1)
            slack_counter += 1
        elif sense == '>=':
            A2.append([-c for c in row])
            b2.append(-rhs)
            s2.append('<=') 
            slack_row_for_pos.append(len(A2) - 1)
            slack_counter += 1
        elif sense == '==':
            A2.append(list(row))
            b2.append(rhs)
            s2.append('<=') 
            slack_row_for_pos.append(len(A2) - 1)
            slack_counter += 1

            A2.append([-c for c in row])
            b2.append(-rhs)
            s2.append('<=') 
            slack_row_for_pos.append(len(A2) - 1)
            slack_counter += 1
        else:
            raise ValueError(f"Unknown sense: {sense}")
    return A2, b2, s2, slack_row_for_pos

def _recover_basis_from_tableau(tableau):
    """Восстановление базиса (unit-столбцы) — как в dual.recover..."""
    if not tableau:
        return []
    m = len(tableau) - 1
    cols = len(tableau[0]) - 1
    basis = [None] * m
    for j in range(cols):
        one_row = None
        is_unit = True
        for i in range(m):
            v = F(tableau[i][j])
            if v == 1:
                if one_row is None:
                    one_row = i
                else:
                    is_unit = False
                    break
            elif v == 0:
                continue
            else:
                is_unit = False
                break
        if is_unit and one_row is not None:
            basis[one_row] = j
    return basis

def gomory_integer_programming(c, A, b, senses=None, max_iter=50, tol=1e-8):
    """
    Чистая реализация метода Гомори (без branch-and-bound).
    - Строит корректные cuts, подставляя вклад slack'ов в коэффициенты исходных переменных.
    - Пропускает строки, приводящие к тривиальным/противоречивым cut'ам.
    - Останавливается, когда найдено целое решение или достигнут max_iter резок.
    """
    current_A = deepcopy(A)
    current_b = deepcopy(b)
    current_senses = deepcopy(senses) if senses else ['<='] * len(A)
    iteration = 0
    n = len(c)

    while iteration < max_iter:
        iteration += 1
        result = dual_simplex(c, current_A, current_b, current_senses)

        if result.status != 'optimal':
            return SimplexResult(result.status, tableau=result.tableau, history=result.history)

        x = result.x
        tableau = result.tableau

        # проверка целочисленности
        frac_idx = None
        for i, xi in enumerate(x):
            if not isclose(xi, round(xi), abs_tol=tol):
                frac_idx = i
                break
        if frac_idx is None:
            return SimplexResult('optimal', x, result.objective, tableau=result.tableau, history=result.history)

        # восстановим A2,b2,s2 и mapping slack_pos -> row_index
        A2, b2, s2, slack_row_for_pos = _preprocess_constraints_local(current_A, current_b, current_senses)
        slack_count = sum(1 for t in s2 if t in ('<=', '>='))

        m = len(tableau) - 1
        cols = len(tableau[0]) - 1

        # Ищем подходящую строку: дробный RHS и при подстановке вклад в исходные переменные не нулевой
        chosen_cut = None
        for i in range(m):
            row = tableau[i]
            rhs = F(row[-1])
            frac_rhs = rhs - F(floor(rhs))
            if frac_rhs <= F(tol):
                continue

            frac_cols = [F(row[j]) - F(floor(F(row[j]))) for j in range(cols)]

            # вычисляем coeffs по исходным переменным с учётом slack-подстановки
            coeffs = [F(0)] * n
            for j in range(n):
                coeffs[j] = frac_cols[j]

            for s_idx in range(slack_count):
                frac_s = frac_cols[n + s_idx] if (n + s_idx) < len(frac_cols) else F(0)
                if frac_s == 0:
                    continue
                slack_row = slack_row_for_pos[s_idx]
                for j in range(n):
                    coeffs[j] -= frac_s * F(A2[slack_row][j])
                frac_rhs -= frac_s * F(b2[slack_row])

            any_coeff_nonzero = any(abs(float(cj)) > tol for cj in coeffs)
            if not any_coeff_nonzero:
                continue

            # имеем рабочий cut: coeffs x >= frac_rhs
            # преобразуем в <=: -coeffs x <= -frac_rhs (оставляем Fraction)
            new_row = [-coeffs[j] for j in range(n)]
            new_rhs = -frac_rhs
            chosen_cut = (new_row, new_rhs, i, coeffs, frac_rhs)
            break

        if chosen_cut is None:
            return SimplexResult('no_valid_gomory_cut', tableau=result.tableau, history=result.history)

        # добавляем выбранный cut
        new_row, new_rhs, row_idx, coeffs_frac, rhs_frac = chosen_cut
        current_A.append(new_row)
        current_b.append(new_rhs)
        current_senses.append('<=') 

    return SimplexResult('max_iter_exceeded', tableau=result.tableau, history=result.history)

def gomory_integer(c, A, b, senses=None, max_cuts=50, tol=1e-8):
    return gomory_integer_programming(c, A, b, senses=senses, max_iter=max_cuts, tol=tol)

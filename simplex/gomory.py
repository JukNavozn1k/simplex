# gomory.py
from copy import deepcopy
from math import floor, isclose
from fractions import Fraction as F
from .dual import dual_simplex, SimplexResult, build_tableau

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
    Выполняет алгоритм Гомори с хранением истории по итерациям.

    Возвращаемый SimplexResult.history теперь является списком объектов-итераций:
    {
        'iteration': k,                                  # номер итерации (начиная с 1)
        'constraints': { 'A': [...], 'b': [...], 'senses': [...] },
        'simplex_history': [tableau0, tableau1, ...],    # история симплекса для этой итерации
        'final_status': 'optimal' | 'infeasible' | ...,   # статус после оптимизации на этой итерации
        'final_tableau': tableau,                         # финальный табло
        'cut_added': { 'row': [...], 'rhs': value } | None
    }
    """

    current_A = deepcopy(A)
    current_b = deepcopy(b)
    current_senses = deepcopy(senses) if senses else ['<='] * len(A)
    iteration = 0
    n = len(c)
    iterations_history = []

    while iteration < max_iter:
        iteration += 1

        # 1) Запускаем симплекс для текущих ограничений
        simplex_res = dual_simplex(c, current_A, current_b, current_senses)

        # Снимок истории симплекса для данной итерации
        iter_record = {
            'iteration': iteration,
            'constraints': {
                'A': deepcopy(current_A),
                'b': deepcopy(current_b),
                'senses': deepcopy(current_senses),
            },
            'simplex_history': deepcopy(getattr(simplex_res, 'history', [])),
            'final_status': simplex_res.status,
            'final_tableau': deepcopy(simplex_res.tableau),
            'cut_added': None,
        }

        # Если не оптимально — заканчиваем и возвращаем историю
        if simplex_res.status != 'optimal':
            iterations_history.append(iter_record)
            return SimplexResult(simplex_res.status, tableau=simplex_res.tableau, history=iterations_history)

        x = simplex_res.x
        tableau = simplex_res.tableau

        # 2) Проверка целочисленности решения
        frac_idx = None
        for i, xi in enumerate(x):
            if not isclose(xi, round(xi), abs_tol=tol):
                frac_idx = i
                break
        if frac_idx is None:
            iterations_history.append(iter_record)
            return SimplexResult('optimal', x, simplex_res.objective, tableau=tableau, history=iterations_history)

        # 3) Построение разреза Гомори на основе текущего табло
        A2, b2, s2, slack_row_for_pos = _preprocess_constraints_local(current_A, current_b, current_senses)
        slack_count = sum(1 for t in s2 if t in ('<=', '>='))

        m = len(tableau) - 1
        cols = len(tableau[0]) - 1

        chosen_cut = None
        for i in range(m):
            row = tableau[i]
            rhs = F(row[-1])
            frac_rhs = rhs - F(floor(rhs))
            if frac_rhs <= F(tol):
                continue

            frac_cols = [F(row[j]) - F(floor(F(row[j]))) for j in range(cols)]

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

            new_row = [-coeffs[j] for j in range(n)]
            new_rhs = -frac_rhs
            chosen_cut = (new_row, new_rhs, i)
            break

        # Если разрез построить не удалось — выходим
        if chosen_cut is None:
            iterations_history.append(iter_record)
            return SimplexResult('no_valid_gomory_cut', tableau=tableau, history=iterations_history)

        # 4) Добавляем разрез и записываем информацию о нём в текущую итерацию,
        # после чего переходим к следующему циклу
        new_row, new_rhs, row_idx = chosen_cut
        iter_record['cut_added'] = {
            'row': [float(v) for v in new_row],
            'rhs': float(new_rhs),
            'source_row_index': row_idx,
        }
        iterations_history.append(iter_record)

        current_A.append(new_row)
        current_b.append(new_rhs)
        current_senses.append('<=')

    # Достигнут лимит
    # Последний iter_record уже добавлен, если мы сюда дошли без возврата —
    # алгоритм не нашёл целочисленного решения в пределах max_iter
    # Вернём статус max_iter_exceeded с накопленной историей
    # Если вдруг simplex_res здесь не определён (например, max_iter == 0),
    # зададим tableau=None
    last_tableau = None
    try:
        last_tableau = deepcopy(simplex_res.tableau)
    except Exception:
        last_tableau = None
    return SimplexResult('max_iter_exceeded', tableau=last_tableau, history=iterations_history)

def gomory_integer(c, A, b, senses=None, max_cuts=50, tol=1e-8):
    return gomory_integer_programming(c, A, b, senses=senses, max_iter=max_cuts, tol=tol)

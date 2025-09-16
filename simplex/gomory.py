from copy import deepcopy
from fractions import Fraction as F

from .dual import dual_simplex, SimplexResult,preprocess_constraints
from fractions import Fraction as F
from copy import deepcopy

def gomory_integer(c_in, A_in, b_in, senses=None, max_cuts=10):
    """
    Исправленный Gomory fractional-cut.
    Использует preprocess_constraints, чтобы корректно подставлять slack'и.
    """
    # копируем входные данные (не мутируем внешние списки)
    c = [F(v) for v in c_in]
    A = [ [F(v) for v in row] for row in A_in ]
    b = [F(v) for v in b_in]
    if senses is None:
        senses = ['<='] * len(b)
    else:
        senses = list(senses)

    # решаем начальную релаксацию (dual_simplex у вас ожидает float)
    res = dual_simplex([float(x) for x in c],
                       [[float(x) for x in row] for row in A],
                       [float(x) for x in b],
                       senses)
    if res.status != 'optimal':
        return res

    # фиксируем initial_slack и original_m для дальнейших пересчётов
    initial_slack = res.slack_count if res.slack_count is not None else (len(res.tableau[0]) - len(c) - 1)
    orig_m = original_m

    cuts = 0
    def frac_part(fr: F) -> F:
        f = fr - F(int(fr))
        if f < 0:
            f += 1
        return f

    while cuts < max_cuts:
        T = res.tableau
        m_rows = len(T) - 1

        # ВАЖНО: получаем предобработанные матрицу/вектор (как это делает simplex)
        A2, b2, s2 = preprocess_constraints([[float(x) for x in row] for row in A],
                                            [float(x) for x in b],
                                            senses)
        # приводим A2,b2 обратно к Fraction (чтобы работать точно)
        A2 = [ [F(v) for v in row] for row in A2 ]
        b2 = [ F(v) for v in b2 ]

        # список индексов строк A2, которым соответствует slack (те строки, где sense in ('<=','>='))
        slack_rows = [i for i, sense in enumerate(s2) if sense in ('<=', '>=')]
        slack_count = len(slack_rows)

        # найти строку с дробным RHS
        row_idx = next((i for i in range(m_rows) if F(T[i][-1]).denominator != 1), None)
        if row_idx is None:
            return SimplexResult('optimal', res.x, res.objective, tableau=res.tableau, history=res.history)

        row = T[row_idx]
        n = len(c)
        cols = len(row) - 1  # число столбцов без RHS (ориг.переменные + slack)
        # дробные части: оригинальные переменные и slack-столбцы (в том же порядке, как в таблице)
        r = [frac_part(F(row[j])) for j in range(n)]
        s = [frac_part(F(row[n + k])) for k in range(slack_count)]
        frac_rhs = frac_part(F(row[-1]))

        # подстановка slack'ов: используем A2 и b2 и mapping slack_rows
        new_A_row = [F(0)] * n
        for j in range(n):
            val = r[j]
            for k in range(slack_count):
                ai_row_idx = slack_rows[k]   # индекс строки в A2, соответствующий k-ому slack
                val -= s[k] * F(A2[ai_row_idx][j])
            new_A_row[j] = val

        new_b = frac_rhs
        for k in range(slack_count):
            ai_row_idx = slack_rows[k]
            new_b -= s[k] * F(b2[ai_row_idx])

        # если разрез тривиален, попробуем следующую дробную строку
        if all(v == 0 for v in new_A_row) and new_b == 0:
            found = False
            for i in range(row_idx + 1, m_rows):
                if F(T[i][-1]).denominator != 1:
                    row = T[i]
                    r = [frac_part(F(row[j])) for j in range(n)]
                    s = [frac_part(F(row[n + k])) for k in range(slack_count)]
                    frac_rhs = frac_part(F(row[-1]))
                    new_A_row = [F(0)] * n
                    for j in range(n):
                        val = r[j]
                        for k in range(slack_count):
                            ai_row_idx = slack_rows[k]
                            val -= s[k] * F(A2[ai_row_idx][j])
                        new_A_row[j] = val
                    new_b = frac_rhs
                    for k in range(slack_count):
                        ai_row_idx = slack_rows[k]
                        new_b -= s[k] * F(b2[ai_row_idx])
                    if not (all(v == 0 for v in new_A_row) and new_b == 0):
                        found = True
                        break
            if not found:
                return res

        # приводим разрез к форме <= (удобно для preprocess_constraints)
        # исходный: sum_j new_A_row[j] * x_j >= new_b
        # умножаем на -1 -> sum_j (-new_A_row[j]) * x_j <= -new_b
        A.append([ -float(v) for v in new_A_row ])
        b.append(float(-new_b))
        senses.append('<=')  # добавили в форме <=

        # решаем релаксацию снова
        res = dual_simplex([float(x) for x in c],
                           [[float(x) for x in row] for row in A],
                           [float(x) for x in b],
                           senses)
        if res.status != 'optimal':
            return res

        cuts += 1

    return res

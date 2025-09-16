# gomory.py
from copy import deepcopy
from math import floor, isclose
from .dual import dual_simplex, SimplexResult

def gomory_integer_programming(c, A, b, senses=None, max_iter=50, tol=1e-8):
    """
    Метод Гомори для целочисленного решения задачи LP.
    Использует dual_simplex из dual.py как подалгоритм.
    Статусы совпадают с dual_simplex: 'optimal', 'infeasible', 'unbounded'.
    Добавлен статус 'max_iter_exceeded' при превышении итераций.
    """
    current_A = deepcopy(A)
    current_b = deepcopy(b)
    current_senses = deepcopy(senses) if senses else ['<='] * len(A)
    iteration = 0

    while iteration < max_iter:
        iteration += 1
        result = dual_simplex(c, current_A, current_b, current_senses)

        if result.status != 'optimal':
            # возвращаем статус dual_simplex без изменений
            return SimplexResult(result.status, tableau=result.tableau, history=result.history)

        x = result.x

        # Находим первую дробную переменную
        frac_idx = None
        for i, xi in enumerate(x):
            if not isclose(xi, round(xi), abs_tol=tol):
                frac_idx = i
                break

        # Все переменные целые
        if frac_idx is None:
            return SimplexResult('optimal', x, result.objective, tableau=result.tableau, history=result.history)

        # Добавляем простую резку Гомори: x_i <= floor(x_i)
        new_row = [0] * len(c)
        new_row[frac_idx] = 1
        current_A.append(new_row)
        current_b.append(floor(x[frac_idx]))
        current_senses.append('<=')

    # Если превысили итерации — возвращаем отдельный статус
    return SimplexResult('max_iter_exceeded', tableau=result.tableau, history=result.history)

def gomory_integer(c, A, b, senses=None, max_cuts=50, tol=1e-8):
    """
    Обертка для совместимости с тестами и UI.
    Параметр max_cuts маппится на max_iter у gomory_integer_programming.
    Поддерживает те же статусы, что и dual_simplex.
    """
    return gomory_integer_programming(c, A, b, senses=senses, max_iter=max_cuts, tol=tol)

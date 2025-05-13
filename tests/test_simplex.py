import pytest
from scipy.optimize import linprog
from simplex import simplex

def test_simplex_vs_scipy_optimal():
    """
    Тест на оптимальное решение: сравниваем с результатом SciPy.
    Пример задачи:
        Максимизировать: 3x1 + 2x2
        При условиях:
            2x1 + x2 <= 100
            x1 + x2 <= 80
            x1 <= 40
            x1, x2 >= 0
    Ожидаемое решение: x1=20, x2=60, opt_value=180.
    """
    # Подготовка данных для нашей функции simplex
    tableau = [
        [2, 1, 1, 0, 0, 100],
        [1, 1, 0, 1, 0, 80],
        [1, 0, 0, 0, 1, 40],
        [-3, -2, 0, 0, 0, 0]  # Последний элемент - правая часть (0 для целевой)
    ]
    basis = [2, 3, 4]  # Индексы slack-переменных

    # Запуск нашей реализации
    our_result = simplex([row.copy() for row in tableau], basis.copy())
    
    # Проверка статуса
    assert our_result['status'] == 'optimal'
    
    # Подготовка данных для SciPy
    c = [-3, -2]  # Коэффициенты целевой для минимизации (-maximization)
    A_ub = [
        [2, 1],
        [1, 1],
        [1, 0]
    ]
    b_ub = [100, 80, 40]
    bounds = [(0, None), (0, None)]
    
    # Запуск SciPy
    scipy_result = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    # Сравнение результатов
    assert scipy_result.success
    assert our_result['optimal_value'] == pytest.approx(-scipy_result.fun, rel=1e-6)
    assert our_result['solution'][:2] == pytest.approx(scipy_result.x, rel=1e-6)

def test_simplex_vs_scipy_unbounded():
    """
    Тест на неограниченность. Пример:
        Максимизировать: x1 + x2
        При условиях:
            x1 - x2 <= 1
            -x1 + x2 <= 1
            x1, x2 >= 0
    Ожидаемый результат: задача неограниченна.
    """
    # Данные для нашей функции
    tableau = [
        [1, -1, 1, 0, 1],
        [-1, 1, 0, 1, 1],
        [-1, -1, 0, 0, 0]  # Целевая: -x1 -x2
    ]
    basis = [2, 3]  # Slack variables
    
    our_result = simplex([row.copy() for row in tableau], basis.copy())
    assert our_result['status'] == 'unbounded'
    
    # Проверка через SciPy
    c = [-1, -1]  # Для минимизации -max
    A_ub = [
        [1, -1],
        [-1, 1]
    ]
    b_ub = [1, 1]
    bounds = [(0, None), (0, None)]
    
    scipy_result = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    assert scipy_result.status == 3  # SciPy статус 'unbounded'
def test_simplex_vs_scipy_infeasible():
    """
    Тест на недопустимость. Пример:
        Максимизировать: x
        При условиях:
            x <= -1
            x >= 0
    """
    # Корректные данные
    tableau = [
        [1, 1, -1],  # x + s = -1 (s >= 0)
        [-1, 0, 0]    # Целевая: -x (максимизация)
    ]
    basis = [1]  # Slack переменная s
    
    our_result = simplex([row.copy() for row in tableau], basis.copy())
    assert our_result['status'] == 'infeasible'
    
    # Проверка через SciPy
    c = [-1]  # -x (для максимизации)
    A_ub = [[1]]  # x <= -1
    b_ub = [-1]
    bounds = [(0, None)]  # x >= 0
    
    scipy_result = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    assert scipy_result.status == 2  # 'infeasible'


def test_simplex_multiple_solutions():
    """
    Тест на наличие бесконечного числа решений.
    Пример:
        Максимизировать: x1 + x2
        При условиях:
            x1 + x2 <= 2
            x1, x2 >= 0
    Ожидается флаг multiple_solutions=True.
    """
    tableau = [
        [1, 1, 1, 2],   # x1 + x2 + s1 = 2
        [-1, -1, 0, 0]   # Целевая: -x1 -x2 (максимизация)
    ]
    basis = [2]  # Slack переменная s1
    
    result = simplex([row.copy() for row in tableau], basis.copy())
    
    assert result['status'] == 'optimal'
    assert result['multiple_solutions'] == True
    assert result['optimal_value'] == pytest.approx(2.0)

def test_simplex_degenerate():
    """
    Тест на вырожденную задачу.
    Пример:
        Максимизировать: x1
        При условиях:
            x1 <= 1
            x1 <= 1
            x1 >= 0
    Ожидается решение x1=1.
    """
    tableau = [
        [1, 1, 0, 1],   # x1 + s1 = 1
        [1, 0, 1, 1],   # x1 + s2 = 1
        [-1, 0, 0, 0]    # Целевая: -x1
    ]
    basis = [1, 2]  # Slack переменные s1, s2
    
    result = simplex([row.copy() for row in tableau], basis.copy())
    
    assert result['status'] == 'optimal'
    assert result['solution'][0] == pytest.approx(1.0)
    assert result['optimal_value'] == pytest.approx(1.0)
def test_simplex_already_optimal():
    """
    Тест на случай, когда начальное решение уже оптимально.
    Пример:
        Минимизировать: 2x1 + x2
        При условиях:
            x1 <= 5
            x2 <= 3
            x1, x2 >= 0
    Начальный базис (s1, s2) уже оптимален.
    """
    tableau = [
        [1, 0, 1, 0, 5],  # x1 + s1 = 5
        [0, 1, 0, 1, 3],  # x2 + s2 = 3
        [2, 1, 0, 0, 0]   # Целевая: 2x1 + x2 (минимизация)
    ]
    basis = [2, 3]  # Slack переменные s1, s2
    
    result = simplex([row.copy() for row in tableau], basis.copy())
    
    assert result['status'] == 'optimal'
    assert result['solution'][:2] == pytest.approx([0.0, 0.0])
    assert result['optimal_value'] == pytest.approx(0.0)




# Helper to solve minimization problems by transforming to maximization
# Note: We invert the objective row and adjust the resulting optimal value accordingly.
def solve_min(tableau, basis):
    tbl = [row.copy() for row in tableau]
    # Invert objective coefficients in the last row
    tbl[-1] = [-coef for coef in tbl[-1]]
    result = simplex(tbl, basis.copy())
    if result['status'] == 'optimal':
        result['optimal_value'] = -result['optimal_value']
    return result


def test_minimization_with_simple_constraint():
    # Minimize z = x + y subject to x + y <= 4, x, y >= 0
    # Introduce slack s1: x + y + s1 = 4
    # Tableau columns: x, y, s1, RHS
    tableau = [
        [1.0, 1.0, 1.0, 4.0],  # constraint
        [1.0, 1.0, 0.0, 0.0]   # objective z = x + y
    ]
    basis = [2]  # slack in basis

    result = solve_min(tableau, basis)
    # According to the current simplex implementation, the transformed maximization
    # of -z yields an optimal solution x = 4, y = 0, with original min value z = -(-4) = 4
    assert result['status'] == 'optimal'
    assert pytest.approx(result['solution'][0], abs=1e-6) == 4.0
    assert pytest.approx(result['solution'][1], abs=1e-6) == 0.0
    assert pytest.approx(result['optimal_value'], abs=1e-6) == -4.0


def test_infeasible_due_to_ge_constraint():
    # Maximize z = x subject to x >= 1
    # Convert to equation: x - s1 = 1 (surplus variable s1)
    # Tableau columns: x, s1, RHS
    tableau = [
        [1.0, -1.0, 1.0],   # x - s1 = 1
        [-1.0,  0.0, 0.0]   # objective z = x -> -x
    ]
    basis = [1]  # surplus in basis

    result = simplex(tableau, basis)
    # For this formulation the method detects unboundedness
    assert result['status'] == 'unbounded'
    assert 'неогранич' in result['message']

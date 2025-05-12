import pytest
import numpy as np
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
        Ожидаемый результат: нет допустимых решений.
    """
    # Данные для нашей реализации
    tableau = [
        [1, 1, -1],  # x + s = -1 (s >= 0)
        [0, 1, 0, 5], # Другое ограничение для заполнения (не используется)
        [-1, 0, 0]    # Целевая: -x
    ]
    basis = [1, 2]  # Slack переменные
    
    our_result = simplex(tableau, basis)
    assert our_result['status'] == 'infeasible'
    
    # Проверка через SciPy
    c = [-1]  # -x (для максимизации)
    A_ub = [[1]]  # x <= -1
    b_ub = [-1]
    bounds = [(0, None)]  # x >= 0
    
    scipy_result = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    assert scipy_result.status == 2  # SciPy статус 'infeasible'
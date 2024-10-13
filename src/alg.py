import numpy as np

def simplex(c, A, b):
    """
    Реализация симплекс-метода для задачи линейного программирования:
    Максимизировать: c^T * x
    При условиях: A * x <= b, x >= 0
    
    Аргументы:
    c -- коэффициенты целевой функции (1D numpy array)
    A -- матрица ограничений (2D numpy array)
    b -- правая часть ограничений (1D numpy array)
    
    Возвращает:
    x_opt -- оптимальные значения переменных
    z_opt -- оптимальное значение целевой функции
    status -- Статус (0: Оптимально, 1: Альтернативные решения)
    """
    
    # Количество переменных и ограничений
    m, n = A.shape
    
    # Создаем полную таблицу симплекс метода
    tableau = np.zeros((m+1, n+m+1))
    tableau[:-1, :-1] = np.hstack([A, np.eye(m)])
    tableau[:-1, -1] = b
    tableau[-1, :-1] = np.hstack([-c, np.zeros(m)])
    
    # Основной цикл симплекс метода
    while not all(tableau[-1, :-1] >= 0):
        # Шаг 1: Выбираем входящую переменную (по минимальному элементу в строке c)
        pivot_col = np.argmin(tableau[-1, :-1])
        
        # Шаг 2: Выбираем выходящую переменную (по минимальному отношению b[i] / A[i][pivot_col])
        ratios = tableau[:-1, -1] / tableau[:-1, pivot_col]
        positive_ratios = np.where(tableau[:-1, pivot_col] > 0, ratios, np.inf)
        pivot_row = np.argmin(positive_ratios)
        
        if np.isinf(positive_ratios[pivot_row]):
            raise ValueError("Задача не имеет решений.")
        
        # Шаг 3: Прямоугольный шаг (нормализуем ведущую строку)
        tableau[pivot_row, :] /= tableau[pivot_row, pivot_col]
        
        # Шаг 4: Обновляем остальные строки
        for i in range(m+1):
            if i != pivot_row:
                tableau[i, :] -= tableau[i, pivot_col] * tableau[pivot_row, :]
    
    # Проверка на альтернативные решения
    # Если есть неосновные переменные, которые могут улучшить значение целевой функции
    alternative = (len(tableau[-1, :n]) - np.count_nonzero(tableau[-1, :n])) > n
    

    # Оптимальные переменные
    x_opt = np.zeros(n)
    for i in range(m):
        basic_var_index = np.where(tableau[i, :n] == 1)[0]
        if len(basic_var_index) == 1:
            x_opt[basic_var_index[0]] = tableau[i, -1]
    
    z_opt = tableau[-1, -1]
    
    # Статус решения (0 - оптимум, 1 - альтернативные решения)
    status = 1 if alternative else 0
    
    return x_opt, z_opt, status

# Пример использования
c = np.array([3, 2])  # Коэффициенты целевой функции
A = np.array([[1, 2], [2, 1], [1, 0]])  # Ограничения
b = np.array([4, 5, 3])  # Правая часть ограничений

x_opt, z_opt, status = simplex(c, A, b)

print("Оптимальные значения переменных:", x_opt)
print("Оптимальное значение целевой функции:", z_opt)
if status == 1:
    print("Существуют альтернативные оптимальные решения.")
else:
    print("Альтернативных решений нет.")

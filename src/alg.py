import math

def simplex(A, b, F):
    # Приведение неравенств к равенствам
    for i in range(len(A)):
        for j in range(len(A)):
            if j == i:
                if b[i] > 0:
                    A[i].append(1)
                else: 
                    A[i].append(-1)
                    b[i] *= -1
            else: 
                A[i].append(0)
    
    # Добавление столбца b в матрицу A
    for i in range(len(A)):
        A[i].append(b[i])

    # Преобразование целевой функции F
    F = [-1 * f for f in F]
    F += [0] * (len(A[0]) - len(F))  # Добавляем дополнительные нули
    A.append(F)  # Добавляем целевую функцию в таблицу

    while min(A[-1][:-1]) < 0:  # Пока есть отрицательные элементы в строке F
        # Находим опорный столбец
        pivot_col = A[-1][:-1].index(min(A[-1][:-1]))

        # Формируем столбец для вычисления отношений
        column = [A[i][pivot_col] for i in range(len(A) - 1)]
        
        # Проверка на то, что задача неограничена
        if max(column) <= 0:
            raise Exception('Задача неограничена')

        # Вычисляем отношения (отношение свободного члена к элементам столбца)
        ratios = [A[i][-1] / column[i] if column[i] > 0 else math.inf for i in range(len(column))]

        if min(ratios) == math.inf:
            raise Exception('Ошибка: Решения нет')

        # Находим опорную строку
        pivot_row = ratios.index(min(ratios))

        # Опорный элемент
        pivot = A[pivot_row][pivot_col]

        # Обновление опорной строки (делим на опорный элемент)
        A[pivot_row] = [x / pivot for x in A[pivot_row]]

        # Обновление остальных строк
        for i in range(len(A)):
            if i != pivot_row:
                factor = A[i][pivot_col]
                A[i] = [A[i][j] - factor * A[pivot_row][j] for j in range(len(A[0]))]

    # Оптимальное решение находится в последнем столбце
    solution = [0] * (len(A[0]) - 1)
    for i in range(len(A) - 1):
        if 1 in A[i][:-1]:
            col_idx = A[i].index(1)
            if all(A[j][col_idx] == 0 for j in range(len(A)) if j != i):
                solution[col_idx] = A[i][-1]
    
    return solution, A[-1][-1]  # Возвращаем оптимальное решение и значение целевой функции




# A коэффиценты при неравенствах
# b свободные члены
# F целевая функция

A = [[1,2],[2,123]]
b = [1,1]
F  = [1,15]
print(simplex(A,b,F))
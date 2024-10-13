import math
def simplex(A,b,F): 
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
    # Приведение неравенств к равенствам
   # Крафт симплекс таблицы 
    for i in range(len(A)):
        A[i].append(b[i])
    F = [-1*f for f in F]
    F += [0]*(len(A)+1)
    A.append(F)
    
   
    while min(A[-1][:-1]) < 0: 
  
        pivot_col = F.index(min(A[-1][:-1]))
        column = [A[i][pivot_col] for i in range(len(A)-1)]
        
        # Проверка на то, что задача неограничена
        if max([A[i][pivot_col] for i in range(len(A))]) <= 0: 
            raise Exception('Задача неограничена ')
        # Проверка на то, что задача неограничена

        ratios = [b[i] / column[i] if b[i] > 0 and column[i] > 0 else math.inf for i in range(len(column))]
        if min(ratios) == math.inf: raise Exception('Ошибка: Решения нет')
        pivot_row = ratios.index(min(ratios))   


        





# A коэффиценты при неравенствах
# b свободные члены
# F целевая функция

A = [[1,2],[2,5]]
b = [1,1]
F  = [1,15]
simplex(A,b,F)
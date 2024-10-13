def simplex(A,b,F): 
    # Приведение неравенств к равенствам
    for i in range(len(A)):
        for j in range(len(A)):
            if j == i:
                if b[i] > 0:
                    A[i].append(1)
                else: A[i].append(-1)
            else: 
                A[i].append(0)
    # Приведение неравенств к равенствам
    for a in A:
        print(a)
    F = [-1*f for f in F]
    while min(F) < 0: 
  
        pivot_col = F.index(min(F))
        column = [A[i][pivot_col] for i in range(len(A))]
        
        # Проверка на то, что задача неограничена
        if max(column) <= 0: 
            raise Exception('Задача неограничена ')
        # Проверка на то, что задача неограничена

        ratios = [b[i] / column[i] if b[i] > 0 and column[i] > 0 else 0 for i in range(len(column))]
        




# A коэффиценты при неравенствах
# b свободные члены
# F целевая функция

A = [[1,2],[2,4],[5,6]]
b = [1,1,1]
F  = [1,1]
simplex(A,b,F)
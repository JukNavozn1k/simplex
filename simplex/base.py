def simplex(tableau, basis):
    m = len(tableau) - 1
    n = len(tableau[0]) - 1
    epsilon = 1e-8
    tableau_history = []

    def copy_tableau():
        return [row.copy() for row in tableau]
    
    tableau_history.append(copy_tableau())
    
    while True:
        last_row = tableau[-1]
        negative_cols = [i for i, val in enumerate(last_row[:-1]) if val < -epsilon]
        
        # В цикле выбора pivot_col:
        if not negative_cols:
            # Проверяем, есть ли отрицательные правые части в ограничениях
            infeasible = any(tableau[i][-1] < -epsilon for i in range(m))
            if infeasible:
                return {{
                'status': 'infeasible',
                'message': 'Задача неограниченна',
                'tableau': copy_tableau(),
                'tableau_history': tableau_history}}
            else:
                break  # Оптимальное решение
            
        pivot_col = max(negative_cols, key=lambda i: abs(last_row[i]))
        
        positive_vals = []
        valid_rows = []
        for i in range(m):
            a = tableau[i][pivot_col]
            b = tableau[i][-1]
            if a > epsilon and b >= -epsilon:  # Проверяем b >= 0
                positive_vals.append(a)
                valid_rows.append(i)
            else:
                positive_vals.append(0)
        
        if all(val <= 0 for val in positive_vals):
            return {
                'status': 'unbounded',
                'message': 'Задача неограниченна',
                'tableau': copy_tableau(),
                'tableau_history': tableau_history
            }
        
        min_ratio = float('inf')
        pivot_row = -1
        for i in valid_rows:  # Только строки с a > 0 и b >= 0
            a = tableau[i][pivot_col]
            b = tableau[i][-1]
            ratio = b / a
            if ratio < min_ratio - epsilon or (
                abs(ratio - min_ratio) < epsilon and a > tableau[pivot_row][pivot_col] if pivot_row != -1 else 0):
                min_ratio = ratio
                pivot_row = i
        
        if pivot_row == -1:
            return {
                'status': 'infeasible',
                'message': 'Нет допустимых решений',
                'tableau': copy_tableau(),
                'tableau_history': tableau_history
            }
        
        basis[pivot_row] = pivot_col
        
        pivot_val = tableau[pivot_row][pivot_col]
        tableau[pivot_row] = [x / pivot_val for x in tableau[pivot_row]]
        
        for i in range(m + 1):
            if i == pivot_row:
                continue
            factor = tableau[i][pivot_col]
            for j in range(n + 1):
                tableau[i][j] -= factor * tableau[pivot_row][j]
        
        tableau_history.append(copy_tableau())
    
    non_basis = set(range(n)) - set(basis)
    multiple = any(abs(tableau[-1][j]) < epsilon for j in non_basis)
    
    solution = [0.0] * n
    for i in range(m):
        col = basis[i]
        solution[col] = tableau[i][-1]
    
    
    opt_value = tableau[-1][-1]  # Убираем минус
    
    return {
        'status': 'optimal',
        'solution': solution,
        'optimal_value': opt_value,
        'multiple_solutions': multiple,
        'tableau': copy_tableau(),
        'tableau_history': tableau_history
    }

from simplex import simplex

# Пример использования с выводом таблицы
if __name__ == "__main__":
    tableau = [
        [2, 1, 1, 0, 4],
        [1, 2, 0, 1, 3],
        [-3, -2, 0, 0, 0]
    ]
    basis = [2, 3]
    
    result = simplex(tableau, basis)
    
    print("Финальная симплекс-таблица:")
    for row in result['tableau']:
        print([round(x, 2) for x in row])
    
    print("\nИстория изменений таблицы:")
    for i, t in enumerate(result['tableau_history']):
        print(f"Iteration {i}:")
        for row in t:
            print([round(x, 2) for x in row])
        print()
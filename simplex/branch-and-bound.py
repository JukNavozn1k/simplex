import heapq
import copy

from .base import simplex

def add_leq_constraint(tableau, basis, var_index, k):
    new_tableau = copy.deepcopy(tableau)
    new_basis = copy.deepcopy(basis)
    
    for row in new_tableau:
        row.insert(-1, 0.0)
    
    new_row = [0.0] * (len(new_tableau[0]) - 1)
    new_row[var_index] = 1.0
    new_row[-2] = 1.0
    new_row.append(k)
    
    new_tableau.insert(-1, new_row)
    new_basis.append(len(new_tableau[0]) - 2)
    
    return new_tableau, new_basis

def add_geq_constraint(tableau, basis, var_index, k):
    new_tableau = copy.deepcopy(tableau)
    new_basis = copy.deepcopy(basis)
    
    for row in new_tableau:
        row.insert(-1, 0.0)
    
    new_row = [0.0] * (len(new_tableau[0]) - 1)
    new_row[var_index] = 1.0
    new_row[-2] = -1.0
    new_row.append(k)
    
    new_tableau.insert(-1, new_row)
    new_basis.append(len(new_tableau[0]) - 2)
    
    return new_tableau, new_basis

def branch_and_bound(initial_tableau, initial_basis, integer_vars, epsilon=1e-8):
    best_value = -float('inf')
    best_solution = None
    node_id = 0
    heap = []
    
    initial_result = simplex(copy.deepcopy(initial_tableau), copy.deepcopy(initial_basis))
    if initial_result['status'] != 'optimal':
        return {
            'status': initial_result['status'],
            'message': initial_result.get('message', ''),
            'optimal_solution': None,
            'optimal_value': None
        }
    
    solution = initial_result['solution']
    if all(abs(solution[i] - round(solution[i])) < epsilon for i in integer_vars if i < len(solution)):
        return {
            'status': 'optimal',
            'optimal_solution': solution,
            'optimal_value': initial_result['optimal_value']
        }
    
    heapq.heappush(heap, (-initial_result['optimal_value'], node_id, initial_tableau, initial_basis))
    node_id += 1

    while heap:
        current_neg_opt, _, tableau, basis = heapq.heappop(heap)
        current_opt = -current_neg_opt

        if current_opt < best_value - epsilon:
            continue

        result = simplex(copy.deepcopy(tableau), copy.deepcopy(basis))
        if result['status'] != 'optimal':
            continue

        opt_val = result['optimal_value']
        solution = result['solution']

        if opt_val < best_value - epsilon:
            continue

        is_integer = True
        branch_var = -1
        for i in integer_vars:
            if i >= len(solution):
                continue
            val = solution[i]
            if abs(val - round(val)) > epsilon:
                is_integer = False
                branch_var = i
                break

        if is_integer:
            if opt_val > best_value + epsilon:
                best_value = opt_val
                best_solution = solution
            continue

        if branch_var == -1:
            continue

        val = solution[branch_var]
        floor_val = int(val)
        ceil_val = floor_val + 1

        new_tableau_leq, new_basis_leq = add_leq_constraint(tableau, basis, branch_var, floor_val)
        result_leq = simplex(copy.deepcopy(new_tableau_leq), copy.deepcopy(new_basis_leq))
        if result_leq['status'] == 'optimal' and result_leq['optimal_value'] >= best_value - epsilon:
            heapq.heappush(heap, (-result_leq['optimal_value'], node_id, new_tableau_leq, new_basis_leq))
            node_id += 1

        new_tableau_geq, new_basis_geq = add_geq_constraint(tableau, basis, branch_var, ceil_val)
        result_geq = simplex(copy.deepcopy(new_tableau_geq), copy.deepcopy(new_basis_geq))
        if result_geq['status'] == 'optimal' and result_geq['optimal_value'] >= best_value - epsilon:
            heapq.heappush(heap, (-result_geq['optimal_value'], node_id, new_tableau_geq, new_basis_geq))
            node_id += 1

    if best_solution is not None:
        return {
            'status': 'optimal',
            'optimal_solution': best_solution,
            'optimal_value': best_value
        }
    else:
        return {
            'status': 'infeasible',
            'message': 'Целочисленное решение не найдено',
            'optimal_solution': None,
            'optimal_value': None
        }
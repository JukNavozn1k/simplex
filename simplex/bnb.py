from copy import deepcopy
from .dual import dual_simplex as simplex, SimplexResult, recover_basis_from_tableau
import math

class BnBResult:
    def __init__(self, status, x=None, objective=None, tableau=None, history=None, final_constraints=None, tree=None):
        self.status = status        # 'optimal' или 'infeasible'
        self.x = x or []
        self.objective = objective
        self.tableau = tableau
        # История итераций для BnB не нужна; не сохраняем
        self.history = []
        
        self.final_constraints = final_constraints
        # Дерево ветвлений: узлы с левой/правой ветвью и информацией LP в каждом узле
        self.tree = tree

def branch_and_bound(c, A, b, senses, best=None, depth=0, max_depth=50, added_A=None, added_b=None, added_s=None, tree_root=None, current_node=None, branch_info=None):
    """Внутренний B&B: все ограничения — только '<=' или '=='."""
    if depth > max_depth:
        # Возвращаем best, но с прикреплённым деревом
        if best is not None:
            best.tree = tree_root
            return best
        return BnBResult('infeasible', tree=tree_root)

    # решаем LP для текущего узла
    lp = simplex(c, A, b, senses)

    # Инициализация корня/обновление текущего узла независимо от статуса LP
    if tree_root is None:
        tree_root = {
            'type': 'root',
            'depth': depth,
            'var': None,
            'bound': None,
            'lp_objective': lp.objective if lp.status == 'optimal' else None,
            'tableau': deepcopy(lp.tableau),
            'basis': recover_basis_from_tableau(lp.tableau) if lp.tableau else [],
            'left': None,
            'right': None,
            'status': lp.status,
        }
        current_node = tree_root
    else:
        if current_node is not None:
            current_node['lp_objective'] = lp.objective if lp.status == 'optimal' else None
            current_node['tableau'] = deepcopy(lp.tableau)
            current_node['basis'] = recover_basis_from_tableau(lp.tableau) if lp.tableau else []
            current_node['status'] = lp.status

    if lp.status != 'optimal':
        # Узел несовместен или неограничен — возвращаем текущий best, но дерево уже создано
        if best is not None:
            best.tree = tree_root
            return best
        return BnBResult(lp.status, tree=tree_root)

    x_relaxed, obj_relaxed = lp.x, lp.objective
    if best is not None and obj_relaxed <= best.objective:
        best.tree = tree_root
        return best

    # Найти первую дробную переменную
    for i in range(len(x_relaxed)):
        if abs(x_relaxed[i] - round(x_relaxed[i])) > 1e-9:
            break
    else:
        # Заполняем информацию текущего узла (LP-решение) в дереве
        if current_node is not None:
            current_node['lp_objective'] = obj_relaxed
            current_node['tableau'] = deepcopy(lp.tableau)
            current_node['basis'] = recover_basis_from_tableau(lp.tableau)

        # Целочисленное решение найдено
        res = BnBResult(
            'optimal',
            [int(round(v)) for v in x_relaxed],
            obj_relaxed,
            tableau=lp.tableau,
            history=None,
            final_constraints=(deepcopy(added_A or []), deepcopy(added_b or []), list(added_s or [])),
            tree=tree_root,
        )
        return res

    xi = x_relaxed[i]
    fl = math.floor(xi)
    ce = math.ceil(xi)

    # Инициализируем списки добавленных ограничений (только ветвления)
    if added_A is None:
        added_A, added_b, added_s = [], [], []

    # К этому моменту дерево уже инициализировано выше и узел обновлён

    # LE-ветвь:  x_i <= floor(xi)
    A1, b1, s1 = deepcopy(A), deepcopy(b), list(senses)
    row1 = [0]*len(c); row1[i] = 1
    A1.append(row1); b1.append(fl); s1.append('<=')
    added_A1 = deepcopy(added_A) + [row1]
    added_b1 = deepcopy(added_b) + [fl]
    added_s1 = list(added_s) + ['<=']
    # Создаём левый дочерний узел в дереве
    left_node = {
        'type': 'LE',
        'depth': depth + 1,
        'var': i,
        'bound': fl,
        'lp_objective': None,
        'tableau': None,
        'basis': None,
        'left': None,
        'right': None,
    }
    if current_node is not None:
        current_node['left'] = left_node
    best = branch_and_bound(c, A1, b1, s1, best, depth+1, max_depth, added_A1, added_b1, added_s1, tree_root=tree_root, current_node=left_node)

    # GE-ветвь через <=:  -x_i <= -ceil(xi)
    A2, b2, s2 = deepcopy(A), deepcopy(b), list(senses)
    row2 = [0]*len(c); row2[i] = -1
    A2.append(row2); b2.append(-ce); s2.append('<=')
    added_A2 = deepcopy(added_A) + [row2]
    added_b2 = deepcopy(added_b) + [-ce]
    added_s2 = list(added_s) + ['<=']
    # Создаём правый дочерний узел в дереве
    right_node = {
        'type': 'GE',
        'depth': depth + 1,
        'var': i,
        'bound': ce,
        'lp_objective': None,
        'tableau': None,
        'basis': None,
        'left': None,
        'right': None,
    }
    if current_node is not None:
        current_node['right'] = right_node
    best = branch_and_bound(c, A2, b2, s2, best, depth+1, max_depth, added_A2, added_b2, added_s2, tree_root=tree_root, current_node=right_node)

    if best is not None:
        best.tree = tree_root
    return best

def solve_integer(c, A, b, senses=None):
    """
    max c^T x
    s.t. A x (<=,>=,==) b  — любые исходные типы
         x целые, x >= 0
    """
    orig_s = senses or ['<='] * len(A)
    A0, b0, s0 = deepcopy(A), deepcopy(b), list(orig_s)

    # Инициализируем корень дерева внутри branch_and_bound
    res = branch_and_bound(c, A0, b0, s0)

    if res is None:
        # На всякий случай; сейчас branch_and_bound всегда возвращает BnBResult
        out = SimplexResult('infeasible')
        out.bnb_tree = None
        return out, None

    # Формируем единый SimplexResult для любых статусов, обязательно прикладывая дерево
    out = SimplexResult(res.status, res.x, res.objective, tableau=res.tableau, history=None)
    out.final_constraints = res.final_constraints
    out.bnb_tree = res.tree
    return out, res.x


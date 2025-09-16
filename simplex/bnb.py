from copy import deepcopy
from .dual import dual_simplex as simplex, SimplexResult
import math

class BnBResult:
    def __init__(self, status, x=None, objective=None, tableau=None, history=None, final_constraints=None):
        self.status = status        # 'optimal' или 'infeasible'
        self.x = x or []
        self.objective = objective
        # финальная симплекс-таблица и история итераций для LP на узле,
        # где найдено целочисленное решение (если найдено)
        self.tableau = tableau
        self.history = history or []
        # сохранённые ограничения (A, b, senses) для финального узла
        self.final_constraints = final_constraints

def branch_and_bound(c, A, b, senses, best=None, depth=0, max_depth=50, added_A=None, added_b=None, added_s=None):
    """Внутренний B&B: все ограничения — только '<=' или '=='."""
    if depth > max_depth:
        return best or BnBResult('infeasible')

    # решаем LP для текущего узла
    lp = simplex(c, A, b, senses)
    if lp.status != 'optimal':
        return best

    x_relaxed, obj_relaxed = lp.x, lp.objective
    if best is not None and obj_relaxed <= best.objective:
        return best

    # Найти первую дробную переменную
    for i in range(len(x_relaxed)):
        if abs(x_relaxed[i] - round(x_relaxed[i])) > 1e-9:
            break
    else:
        # целочисленное решение найдено на текущем LP-узле
        # возвращаем только добавленные (ветвящие) ограничения, без исходных
        return BnBResult(
            'optimal',
            [int(round(v)) for v in x_relaxed],
            obj_relaxed,
            tableau=lp.tableau,
            history=lp.history,
            final_constraints=(deepcopy(added_A or []), deepcopy(added_b or []), list(added_s or [])),
        )

    xi = x_relaxed[i]
    fl = math.floor(xi)
    ce = math.ceil(xi)

    # Инициализируем списки добавленных ограничений (только ветвления)
    if added_A is None:
        added_A, added_b, added_s = [], [], []

    # LE-ветвь:  x_i <= floor(xi)
    A1, b1, s1 = deepcopy(A), deepcopy(b), list(senses)
    row1 = [0]*len(c); row1[i] = 1
    A1.append(row1); b1.append(fl); s1.append('<=')
    added_A1 = deepcopy(added_A) + [row1]
    added_b1 = deepcopy(added_b) + [fl]
    added_s1 = list(added_s) + ['<=']
    best = branch_and_bound(c, A1, b1, s1, best, depth+1, max_depth, added_A1, added_b1, added_s1)

    # GE-ветвь через <=:  -x_i <= -ceil(xi)
    A2, b2, s2 = deepcopy(A), deepcopy(b), list(senses)
    row2 = [0]*len(c); row2[i] = -1
    A2.append(row2); b2.append(-ce); s2.append('<=')
    added_A2 = deepcopy(added_A) + [row2]
    added_b2 = deepcopy(added_b) + [-ce]
    added_s2 = list(added_s) + ['<=']
    best = branch_and_bound(c, A2, b2, s2, best, depth+1, max_depth, added_A2, added_b2, added_s2)

    return best

def solve_integer(c, A, b, senses=None):
    """
    max c^T x
    s.t. A x (<=,>=,==) b  — любые исходные типы
         x целые, x >= 0
    """
    orig_s = senses or ['<='] * len(A)
    A0, b0, s0 = deepcopy(A), deepcopy(b), list(orig_s)

    # # добавляем x_j >= 0 как -x_j <= 0
    # for j in range(len(c)):
    #     row = [0] * len(c)
    #     row[j] = -1
    #     A0.append(row); b0.append(0); s0.append('<=')

    res = branch_and_bound(c, A0, b0, s0)

    if res is None:
        # Совсем не нашли решений
        return SimplexResult('infeasible'), None
    elif res.status == 'optimal':
        # Пробрасываем финальную таблицу и историю в результат, чтобы UI мог их показать
        out = SimplexResult('optimal', res.x, res.objective, tableau=res.tableau, history=res.history)
        # Дополнительно прикладываем финальные ограничения узла (для возможного отображения)
        out.final_constraints = res.final_constraints
        return out, res.x
    else:
        # на всякий случай, если появятся другие статусы
        out = SimplexResult(res.status, res.x, res.objective, tableau=res.tableau, history=res.history)
        out.final_constraints = res.final_constraints
        return out, res.x


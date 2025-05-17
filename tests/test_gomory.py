# import pytest
# from simplex import gomory_integer   
# try:
#     from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpInteger, value, LpStatus
#     PULP = True
# except ImportError:
#     PULP = False



# def solve_pulp_integer(c, A, b, signs=None):
#     """
#     Решает целочисленную задачу линейного программирования с помощью PuLP.
#     max c^T x
#     s.t. Ax [signs[i]] b
#     x — целочисленное
#     """
#     n = len(c)
#     prob = LpProblem("Integer_MIP", LpMaximize)
#     x = [LpVariable(f"x{i}", lowBound=0, cat=LpInteger) for i in range(n)]
#     prob += lpSum(c[i] * x[i] for i in range(n))
    
#     if signs is None:
#         signs = ["<="] * len(b)
    
#     for row, bi, sign in zip(A, b, signs):
#         if sign == "<=":
#             prob += lpSum(row[i] * x[i] for i in range(n)) <= bi
#         elif sign == ">=":
#             prob += lpSum(row[i] * x[i] for i in range(n)) >= bi
#         elif sign == "==":
#             prob += lpSum(row[i] * x[i] for i in range(n)) == bi
#         else:
#             raise ValueError(f"Unsupported constraint sign: {sign}")
    
#     status_code = prob.solve()
#     status_name = LpStatus[status_code]
#     return status_name, [int(value(xi)) for xi in x]


# @pytest.mark.skipif(not PULP, reason="PuLP не установлен")
# @pytest.mark.parametrize(
#     "c, A, b, expected",
#     [
#         (
#             [2, 3],
#             [[1, 0], [0, 1], [1, 1]],
#             [4, 4, 5],
#             [1, 4]
#         ),
#         (
#             [3, 2, 4],
#             [[1, 1, 1], [2, 0, 1], [0, 1, 2]],
#             [5, 6, 5],
#             [2, 1, 2]
#         ),
#     ]
# )
# def test_gomory_vs_pulp(c, A, b, expected):
#     """
#     Сравниваем решение метода Гомори с решением PuLP.
#     """
#     res = gomory_integer(c.copy(), [row.copy() for row in A], b.copy())
#     assert res.status == 'optimal_integer'
#     assert res.x == expected
#     assert all(isinstance(x, int) for x in res.x)

#     status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
#     assert status_pulp == 'Optimal'
#     assert sol_pulp == expected


# @pytest.mark.skipif(not PULP, reason="PuLP не установлен")
# @pytest.mark.parametrize(
#     "c, A, b, expected_status, expected_solution",
#     [
#         (
#             [2, 3],
#             [[1, 0], [0, 1], [1, 1]],
#             [4, 4, 5],
#             'optimal_integer',
#             [1, 4]
#         ),
#         (
#             [3, 2, 4],
#             [[1, 1, 1], [2, 0, 1], [0, 1, 2]],
#             [5, 6, 5],
#             'optimal_integer',
#             [2, 1, 2]
#         ),
#         (
#             [1, 1],
#             [[1, 2], [3, 4]],
#             [1, 1],
#             'optimal_integer',
#             [0, 0]
#         ),
#         (
#             [1, 1],
#             [[1, 0], [0, 1]],
#             [2, 2],
#             'optimal_integer',
#             [2, 2 ]
#         ),
#         (
#             [-1, -2],
#             [[1, 1], [2, 0]],
#             [3, 4],
#             'optimal_integer',
#             [0, 0]
#         ),
#         (
#             [0, 0],
#             [[1, 0], [0, 1]],
#             [0, 0],
#             'optimal_integer',
#             [0, 0]
#         ),
#     ]
# )
# def test_gomory_extended(c, A, b, expected_status, expected_solution):
#     """
#     Расширенный набор тестов для метода Гомори.
#     """
#     res = gomory_integer(c.copy(), [row.copy() for row in A], b.copy())
#     assert res.status == expected_status
#     if expected_solution is not None:
#         assert res.x == expected_solution
#         assert all(isinstance(x, int) for x in res.x)

#     if expected_status == 'optimal_integer':
#         status_pulp, sol_pulp = solve_pulp_integer(c, A, b)
#         assert status_pulp == 'Optimal'
#         if expected_solution is not None:
#             assert sol_pulp == expected_solution

# @pytest.mark.skipif(not PULP, reason="PuLP не установлен")
# @pytest.mark.parametrize(
#     "c, A, b, signs, expected",
#     [
#         (
#             [2, 3],
#             [[1, 0], [0, 1], [1, 1]],
#             [4, 4, 5],
#             ["<=", "<=", "<="],
#             [1, 4]
#         ),
#         (
#             [1, 2],
#             [[1, 0], [0, 1], [1, 1]],
#             [1, 2, 4],
#             [">=", ">=", ">="],
#             [1, 2]
#         ),
#         (
#             [3, 1],
#             [[1, 2], [3, 4]],
#             [7, 18],
#             ["==", "=="],
#             [2, 3]
#         ),
#         (
#             [1, 1],
#             [[1, 0], [0, 1], [1, 1], [1, -1]],
#             [3, 3, 5, 1],
#             ["<=", ">=", "==", "<="],
#             [2, 3]
#         ),
#     ]
# )
# def test_gomory_various_constraints(c, A, b, signs, expected):
#     # gomory_integer принимает parameter `senses`
#     res = gomory_integer(c.copy(), [row.copy() for row in A], b.copy(), senses=signs)
    
#     # Проверяем, что статус - оптимальный (но если unbounded, то тест возможно нужно подкорректировать)
#     assert res.status in ('optimal_integer', 'optimal'), f"Unexpected status: {res.status}"

#     # Если статус оптимальный, проверяем решение
#     if res.status == 'optimal_integer':
#         assert all(isinstance(x, int) for x in res.x)
#         assert res.x == expected

#     # solve_pulp_integer не принимает senses, вызываем без него
#     status_pulp, sol_pulp = solve_pulp_integer(c, A, b, signs)
#     assert status_pulp == 'Optimal'
#     assert sol_pulp == expected

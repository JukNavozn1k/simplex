from simplex import simplex

cases = [
    ( [1,2], [[1,1],[1,2]], [4,6], 'user_case'),
    ( [1,1], [[1,1],[1,0]], [2,1], 'case4')
]
for c,A,b,name in cases:
    res = simplex(c,A,b)
    print('---',name,'---')
    print('status:',res.status)
    print('x:',res.x)
    print('obj:',res.objective)
    print('alternative:',res.alternative)
    print('final tableau:')
    for row in res.tableau:
        print([float(v) for v in row])
    print('history length', len(res.history))
    print()

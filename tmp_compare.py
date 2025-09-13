from simplex import simplex as base_simplex
from simplex.dual import dual_simplex

cases=[
    ( [1,2], [[1,1],[1,-1],[1,1]], [5,1,5], ['<=','>=','==']),
    ( [-1,-2], [[1,1]], [5], ['<=']),
]
for c,A,b,senses in cases:
    print('CASE',c,A,b,senses)
    try:
        rbase = base_simplex(c,A,b,senses)
        print(' base:', rbase.status, rbase.objective, rbase.x)
    except Exception as e:
        print(' base error',e)
    try:
        rdual = dual_simplex(c,A,b,senses)
        print(' dual:', rdual.status, rdual.objective, rdual.x)
    except Exception as e:
        print(' dual error',e)
    print('---')

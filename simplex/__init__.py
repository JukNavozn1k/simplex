from .dual import dual_simplex as simplex, SimplexResult
from .bnb import solve_integer

# Export new Gomory implementation and keep old name as alias
from .gomory import gomory_simplex
gomory_integer = gomory_simplex

# For backward compatibility with old UI code
bnb = solve_integer

# __all__ = ['simplex', 'SimplexResult', 'solve_integer', 'bnb', 'gomory_simplex', 'gomory_integer']
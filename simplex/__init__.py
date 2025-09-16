from .dual import dual_simplex as simplex, SimplexResult
from .bnb import solve_integer

from .gomory import gomory_integer
# For backward compatibility with old UI code
bnb = solve_integer

# __all__ = ['simplex', 'SimplexResult', 'solve_integer', 'bnb']
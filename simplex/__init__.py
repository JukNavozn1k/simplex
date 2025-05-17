from .base import simplex, SimplexResult
from .bnb import solve_integer
from .dual import dual_simplex
# For backward compatibility with old UI code
bnb = solve_integer

# __all__ = ['simplex', 'SimplexResult', 'solve_integer', 'dual_simplex', 'bnb']
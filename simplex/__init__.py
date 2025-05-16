from .base import simplex, SimplexResult
from .bnb import solve_integer
from .gomory import gomory_cutting_plane,solve_integer_gomory
# For backward compatibility with old UI code
bnb = solve_integer
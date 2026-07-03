import time
from itertools import product
from pysat.solvers import Solver
 
 
def unit_lines(t, n):
    """All distinct unit lines of Z_t^n, each as a sorted tuple of points."""
    words = list(product(range(t), repeat=n))
    lines, seen = [], set()
    for v in product([0, 1], repeat=n):
        if not any(v):
            continue
        for a in words:
            pts = tuple(sorted(
                tuple((a[j] + k * v[j]) % t for j in range(n))
                for k in range(t)
            ))
            if pts not in seen:
                seen.add(pts)
                lines.append(pts)
    return words, lines
 
 
def check_unit_hj(r, t, n, verbose=False, solver_name='g3'):
    """True iff every r-coloring of Z_t^n contains a monochromatic unit line."""
    if t == 1:                      # single point = degenerate mono line
        return True
    words, lines = unit_lines(t, n)
    N = len(words)
    if r >= N:                      # injective coloring (t >= 2)
        return False
    word_index = {w: i for i, w in enumerate(words)}
 
    solver = Solver(name=solver_name)
    if r == 2:
        # one Boolean per word: True = color 1, False = color 0
        for line in lines:
            ids = [word_index[p] + 1 for p in line]
            solver.add_clause(ids)                # not all color 0
            solver.add_clause([-x for x in ids])  # not all color 1
        solver.add_clause([-1])                   # symmetry: word 0 -> color 0
    else:
        # x_{i,j} = 1 iff word i may take color j.  "At most one color"
        # clauses are redundant: see the discussion in the text.
        def var_id(i, j):
            return i * r + j + 1
        for i in range(N):
            solver.add_clause([var_id(i, j) for j in range(r)])
        for line in lines:
            idxs = [word_index[p] for p in line]
            for j in range(r):
                solver.add_clause([-var_id(i, j) for i in idxs])
        solver.add_clause([var_id(0, 0)])         # symmetry: word 0 -> color 0
 
    sat = solver.solve()
    if sat and verbose:
        model = set(solver.get_model())
        print("Witnessing coloring (no monochromatic unit line):")
        for i, w in enumerate(words):
            c = (i + 1 in model) if r == 2 else next(
                j for j in range(r) if var_id(i, j) in model)
            print(f"  {w} -> color {int(c)}")
    solver.delete()
    return not sat
 
 
def compute_unit_hj(t, r, n_max=10):
    """Smallest n <= n_max forcing a monochromatic unit line, else None."""
    for n in range(1, n_max + 1):
        t0 = time.time()
        forced = check_unit_hj(r, t, n)
        print(f"t={t} r={r} n={n}: {'T' if forced else 'F'}"
              f"  ({time.time()-t0:.1f}s)")
        if forced:
            return n
    return None
 
 
if __name__ == "__main__":
    for t in (2, 3, 4, 5):
        print(f"HJ_unit({t},2) = {compute_unit_hj(t, 2, n_max=7)}")

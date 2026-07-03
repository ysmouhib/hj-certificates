"""
Generalized simplex encoder.  Searches for a coloring
cbar : T_n^(t) -> {0,...,r-1} with no monochromatic corner tuple
C_{k,v}, 1 <= k <= K.

Encoding (Section 3.5).  For r = 2: one Boolean variable per cell
and two clauses per corner tuple, forbidding the all-0 and all-1
assignments.  For r >= 3: variables x_{u,j} ("cell u has color j")
with an at-least-one clause per cell and, per tuple and color, one
clause forbidding all t cells from sharing that color.  In both
regimes a unit clause fixes the color of one cell, harmlessly
breaking part of the color symmetry.
"""
from pysat.solvers import Solver


def cells_of(t, n):
    """The cells of T_n^(t): weak compositions of n into t parts."""
    if t == 1:
        return [(n,)]
    return [(a,) + rest
            for a in range(n + 1) for rest in cells_of(t - 1, n - a)]


def corner_tuples(t, n, K):
    for k in range(1, min(K, n) + 1):
        for v in cells_of(t, n - k):
            yield [tuple(v[i] + (k if i == j else 0)
                         for i in range(t)) for j in range(t)]


def solve_simplex(t, n, r, K, solver_name='g42', verbose=False):
    """Return an avoiding coloring of T_n^(t) as a dict, or None."""
    cells = cells_of(t, n)
    nv = nc = 0
    with Solver(name=solver_name) as s:
        def add(clause):
            nonlocal nc
            nc += 1
            s.add_clause(clause)

        if r == 2:                    # one variable per cell
            var = {u: i + 1 for i, u in enumerate(cells)}
            nv = len(cells)
            add([-var[cells[0]]])                 # symmetry breaking
            for tup in corner_tuples(t, n, K):
                add([-var[u] for u in tup])       # not all 1
                add([var[u] for u in tup])        # not all 0
        else:                         # variables x_{u,j}
            var = {(u, j): i * r + j + 1
                   for i, u in enumerate(cells) for j in range(r)}
            nv = r * len(cells)
            for u in cells:                       # at least one color
                add([var[u, j] for j in range(r)])
            add([var[cells[0], 0]])               # symmetry breaking
            for tup in corner_tuples(t, n, K):    # no mono tuple
                for j in range(r):
                    add([-var[u, j] for u in tup])
        if verbose:
            print(f'  ({nv:,} variables, {nc:,} clauses)')
        if not s.solve():
            return None
        model = set(s.get_model())
        if r == 2:
            return {u: int(var[u] in model) for u in cells}
        return {u: next(j for j in range(r) if var[u, j] in model)
                for u in cells}


def write_certificate(coloring, path):
    with open(path, 'w') as f:
        for u in sorted(coloring):
            f.write(' '.join(map(str, u)) + f' {coloring[u]}\n')


if __name__ == '__main__':
    # Table 3.x: the bracket instance (t,r,K) = (3,2,3).
    for n in (4, 6, 8, 10, 20, 30, 50, 100, 200, 400):
        w = solve_simplex(t=3, n=n, r=2, K=3, verbose=(n == 400))
        print(f'n={n}: {"yes" if w else "no"}')
        if w:
            write_certificate(w, f'T{n}_t3_r2_K3.cert')
    # The classical regime K = n produces the record lower bounds.
    # (3,3): HJ(3,3) >= 22 is the n = 21 instance (Theorem hj33-22).
    # CaDiCaL and Glucose stall on it, so it was solved by CryptoMiniSat
    # through its native Python bindings (pycryptosat, 1 thread, ~90 s),
    # reusing the clause generator above verbatim and replacing only the
    # pysat Solver context by pycryptosat.Solver(); the coloring was
    # written with write_certificate(..., 'T21_t3_r3.cert').
    # (4,2): HJ(4,2) >= 14 is the one-weight coloring of Theorem hj42-14,
    # c(w) = chi(<(0,2,3,5), type(w)> mod 26); no search is needed, and
    # its induced T_13 table was written directly to 'T13_t4_r2.cert'.

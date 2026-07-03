"""
SAT encoding of the diagonal conjecture: search for an r-coloring of
[t]^n whose UNIQUE monochromatic combinatorial line is the main
diagonal L_{*...*}.  Every satisfiable instance yields the
unconditional bound HJ(t,r) >= n.
"""
from itertools import product
from pysat.solvers import Solver


def diagonal_only(t, n, r, solver_name='g42'):
    words = list(product(range(1, t + 1), repeat=n))
    var = {(w, j): i * r + j + 1
           for i, w in enumerate(words) for j in range(r)}
    with Solver(name=solver_name) as s:
        for w in words:                           # at least one color
            s.add_clause([var[w, j] for j in range(r)])
        s.add_clause([var[words[0], 0]])          # symmetry breaking
        diag = [tuple([a] * n) for a in range(1, t + 1)]
        for j in range(r):                        # diagonal: mono
            for w, w2 in zip(diag, diag[1:]):
                s.add_clause([-var[w, j], var[w2, j]])
                s.add_clause([var[w, j], -var[w2, j]])
        m = 0
        symbols = list(range(1, t + 1)) + ['*']
        for template in product(symbols, repeat=n):
            if '*' not in template or all(c == '*' for c in template):
                continue
            m += 1                                # other lines: not mono
            line = [tuple(a if c == '*' else c for c in template)
                    for a in range(1, t + 1)]
            for j in range(r):
                s.add_clause([-var[w, j] for w in line])
        print(f"t={t} n={n} r={r}: {m + 1} lines "
              f"({m} forced non-monochromatic)", end='  ->  ')
        print("SATISFIABLE" if s.solve() else "UNSATISFIABLE")


if __name__ == '__main__':
    diagonal_only(t=3, n=4, r=2)   # sanity check at n = HJ(3)
    diagonal_only(t=3, n=5, r=2)   # forced UNSAT by Prop. 3.x

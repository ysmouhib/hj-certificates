"""
Unified SAT encoder for restricted Hales--Jewett instances on the
full cube.

Decides whether [t]^n admits an r-coloring with no monochromatic
line in
  - the bracket family  L^[K]([t]^n)   (<= K active coordinates), or
  - the interval family L^(q)([t]^n)   (active set = union of
                                        <= q intervals).

Encoding: variables x_{w,j} ("word w has color j"); one at-least-one
clause per word; for every line and every color j, one clause
forbidding all t words of the line from having color j.  At-most-one
clauses are redundant for this monotone avoidance property; a unit
clause fixing the color of the first word breaks part of the color
symmetry.
"""
from itertools import combinations, product
from pysat.solvers import Solver   # name='g42' (Glucose),
                                   # name='cd19' (CaDiCaL)


def num_intervals(S):
    """Number of maximal runs of consecutive integers in S."""
    S = sorted(S)
    return 1 + sum(1 for a, b in zip(S, S[1:]) if b > a + 1)


def lines(t, n, family, bound):
    """Yield the lines of L^[K] (family='bracket', bound=K) or of
    L^(q) (family='interval', bound=q) as t-tuples of words."""
    max_active = bound if family == 'bracket' else n
    for k in range(1, max_active + 1):
        for active in combinations(range(n), k):
            if family == 'interval' and num_intervals(active) > bound:
                continue
            inactive = [i for i in range(n) if i not in active]
            for filling in product(range(1, t + 1),
                                   repeat=len(inactive)):
                root = [None] * n
                for i, v in zip(inactive, filling):
                    root[i] = v
                yield tuple(tuple(a if root[i] is None else root[i]
                                  for i in range(n))
                            for a in range(1, t + 1))


def solve(t, n, r, family, bound, solver_name='g42'):
    """Return an avoiding coloring as a dict word -> color, or None."""
    words = list(product(range(1, t + 1), repeat=n))
    var = {(w, j): i * r + j + 1
           for i, w in enumerate(words) for j in range(r)}
    with Solver(name=solver_name) as s:
        for w in words:                           # at least one color
            s.add_clause([var[w, j] for j in range(r)])
        s.add_clause([var[words[0], 0]])          # symmetry breaking
        m = 0
        for line in lines(t, n, family, bound):   # no mono line
            m += 1
            for j in range(r):
                s.add_clause([-var[w, j] for w in line])
        print(f"t={t} n={n} r={r} {family}<={bound}: "
              f"{len(words)} words, {m} lines", end='  ->  ')
        if not s.solve():
            print("UNSAT (every coloring has a monochromatic line)")
            return None
        model = set(s.get_model())
        print("SAT (an avoiding coloring exists)")
        return {w: next(j for j in range(r) if var[w, j] in model)
                for w in words}


if __name__ == '__main__':
    solve(t=3, n=4, r=2, family='interval', bound=1)  # HJ^(1)(3) >= 5
    solve(t=2, n=5, r=3, family='bracket',  bound=2)  # HJ^[2](2,3)>=6

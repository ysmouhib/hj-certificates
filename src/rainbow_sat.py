#!/usr/bin/env python3
"""ah(3,4) >= 25 (Prop 5.9): search for a surjective rainbow-free 24-colouring
of [3]^4 -- no combinatorial line receives three distinct colours -- and verify
any candidate by direct enumeration of all 175 lines."""
import itertools
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

T, N, NCOL = 3, 4, 24

def words_and_lines():
    words = list(itertools.product(range(1, T + 1), repeat=N))
    idx = {w: i for i, w in enumerate(words)}
    L = []
    for root in itertools.product(list(range(1, T + 1)) + ["*"], repeat=N):
        if "*" in root:
            L.append(tuple(idx[tuple(a if a != "*" else s for a in root)] for s in range(1, T + 1)))
    return words, L

def search(solver="cadical153", precedence=True):
    words, L = words_and_lines()
    W = len(words)
    pool = IDPool()
    x = lambda w, c: pool.id(("x", w, c))
    cnf = CNF()
    for w in range(W):
        cnf.append([x(w, c) for c in range(NCOL)])
        for c1 in range(NCOL):
            for c2 in range(c1 + 1, NCOL):
                cnf.append([-x(w, c1), -x(w, c2)])
    for j, (a, b, c) in enumerate(L):   # some two of the three words agree
        e = [pool.id(("e", j, p)) for p in range(3)]
        cnf.append(e)
        for p, (u, v) in enumerate(((a, b), (a, c), (b, c))):
            for col in range(NCOL):
                cnf.append([-e[p], -x(u, col), x(v, col)])
                cnf.append([-e[p], x(u, col), -x(v, col)])
    for c in range(NCOL):               # surjectivity
        cnf.append([x(w, c) for w in range(W)])
    if precedence:                      # value-precedence symmetry breaking
        for w in range(W):
            for c in range(NCOL):
                if c > w: cnf.append([-x(w, c)])
                elif c > 0: cnf.append([-x(w, c)] + [x(v, c - 1) for v in range(w)])
    with Solver(name=solver, bootstrap_with=cnf) as s:
        if not s.solve(): return None
        m = set(s.get_model())
        return [next(c for c in range(NCOL) if x(w, c) in m) for w in range(W)]

def verify(col):
    words, L = words_and_lines()
    assert len(set(col)) == NCOL, "not surjective onto 24 colours"
    rb = [ln for ln in L if len({col[i] for i in ln}) == 3]
    return len(L), rb

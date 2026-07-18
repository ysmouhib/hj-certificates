#!/usr/bin/env python3
"""Unit-line witnesses over Z_t^n (Prop 6.7): search for 2-colourings with no
monochromatic unit line, and the unsatisfiability of Z_3^3."""
import itertools
from pysat.formula import CNF
from pysat.solvers import Solver

def unit_lines(t, n):
    pts = list(itertools.product(range(t), repeat=n))
    idx = {p: i for i, p in enumerate(pts)}
    seen, out = set(), []
    for v in itertools.product((0, 1), repeat=n):
        if not any(v): continue
        for a in pts:
            line = frozenset(tuple((a[i] + k * v[i]) % t for i in range(n)) for k in range(t))
            if line not in seen:
                seen.add(line); out.append(sorted(idx[p] for p in line))
    return pts, out

def cnf_of(lines):
    cnf = CNF()
    for L in lines:
        cnf.append([-(i + 1) for i in L]); cnf.append([i + 1 for i in L])
    return cnf

def witness(t, n, solver="cadical153"):
    pts, lines = unit_lines(t, n)
    with Solver(name=solver, bootstrap_with=cnf_of(lines)) as s:
        if not s.solve(): return pts, lines, None
        m = set(s.get_model())
        return pts, lines, [1 if (i + 1) in m else 0 for i in range(len(pts))]

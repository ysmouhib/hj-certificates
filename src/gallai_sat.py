#!/usr/bin/env python3
"""
gallai_sat.py -- search / forcing for one-dimensional Gallai homothety numbers.

An r-colouring of the window {0,...,N-1} avoids S iff no homothet b + k*S
(k >= 1) inside the window is monochromatic.  `avoid(S, r, N)` returns such a
colouring or None; `force(S, r, N, solvers)` confirms unsatisfiability with
each named pysat solver and returns the log lines.

Used to (re)generate the window certificates in certificates/ and the forcing
logs in logs/ for Table 2.1 and Proposition 2.21 of the thesis.
"""
import hashlib, time
from pysat.formula import CNF
from pysat.solvers import Solver

SOLVERS = ["cadical153", "glucose42", "minisat22"]

def homothets(S, N):
    D = max(S) - min(S); S0 = sorted(x - min(S) for x in S)
    out = []
    k = 1
    while k * D <= N - 1:
        for b in range(N - k * D):
            out.append([b + k * s for s in S0])
        k += 1
    return out

def encode(S, r, N):
    cnf = CNF()
    var = lambda i, c: i * r + c + 1
    for i in range(N):
        cnf.append([var(i, c) for c in range(r)])
        for c1 in range(r):
            for c2 in range(c1 + 1, r):
                cnf.append([-var(i, c1), -var(i, c2)])
    for H in homothets(S, N):
        for c in range(r):
            cnf.append([-var(i, c) for i in H])
    return cnf, var

def cnf_sha256(cnf):
    body = "\n".join(" ".join(map(str, cl)) for cl in sorted(cnf.clauses))
    return hashlib.sha256(body.encode()).hexdigest()

def avoid(S, r, N, solver="cadical153"):
    cnf, var = encode(S, r, N)
    with Solver(name=solver, bootstrap_with=cnf) as s:
        if not s.solve():
            return None
        m = set(s.get_model())
        return [next(c for c in range(r) if var(i, c) in m) for i in range(N)]

def force(S, r, N, solvers=SOLVERS):
    cnf, _ = encode(S, r, N)
    lines = [f"instance: window N={N}, r={r}, S={sorted(S)}; "
             f"{len(cnf.clauses)} clauses, {N*r} variables; "
             f"{len(homothets(S,N))} homothets",
             f"dimacs-sha256: {cnf_sha256(cnf)}"]
    ok = True
    for name in solvers:
        t0 = time.time()
        with Solver(name=name, bootstrap_with=cnf) as s:
            res = s.solve()
        lines.append(f"solver {name}: {'UNSAT' if not res else 'SAT (!!)'}"
                     f"  ({time.time()-t0:.2f}s)")
        ok &= (not res)
    return ok, lines

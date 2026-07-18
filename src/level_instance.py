#!/usr/bin/env python3
"""The level instance I_{omega,n} (Def 5.1) for omega=(0,2,3,5), t=4, r=2 --
counts (Prop 5.2), unsatisfiability at n=14, primal-graph degeneracy, the
MaxSAT dual (minimum number of monochromatic homothets), and the degree-3
GF(2) Nullstellensatz independence check (part of Thm 5.6)."""
import itertools
from pysat.formula import CNF, WCNF
from pysat.solvers import Solver

OMEGA = (0, 2, 3, 5)

def instance(n, omega=OMEGA):
    t = len(omega); M = omega[-1] * n
    def monoid(m):
        vals = set()
        for c in itertools.product(range(m + 1), repeat=t - 1):
            if sum(c) <= m:
                vals.add(sum(o * ci for o, ci in zip(omega[1:], c)))
        return vals
    used = sorted(monoid(n))
    homs = []
    for k in range(1, n + 1):
        for b in sorted(monoid(n - k)):
            H = tuple(b + k * o for o in omega)
            if H[-1] <= M: homs.append(H)
    return used, sorted(set(homs))

def cnf_of(homs):
    cnf = CNF()
    for H in homs:
        cnf.append([-(l + 1) for l in H]); cnf.append([l + 1 for l in H])
    return cnf

def degeneracy(homs, used):
    adj = {u: set() for u in used}
    for H in homs:
        for a in H:
            for b in H:
                if a != b: adj[a].add(b)
    edges = sum(len(v) for v in adj.values()) // 2
    deg, order = 0, dict(adj)
    live = {u: set(v) for u, v in adj.items()}
    while live:
        u = min(live, key=lambda x: len(live[x]))
        deg = max(deg, len(live[u]))
        for w in live[u]: live[w].discard(u)
        del live[u]
    return edges, deg

def maxsat_min_mono(homs, used):
    from pysat.examples.rc2 import RC2
    w = WCNF(); nv = max(used) + 1
    for j, H in enumerate(homs):
        m = nv + j + 1
        w.append([-(l + 1) for l in H] + [m])   # all-1 -> m
        w.append([(l + 1) for l in H] + [m])    # all-0 -> m
        w.append([-m], weight=1)
    with RC2(w) as rc2:
        rc2.compute()
        return rc2.cost

def nullstellensatz_deg3(homs):
    """443 GF(2) indicators P_C = 1 + sum over proper nonempty subsets;
    check linear independence and 1 not in span (degree-3 part of Thm 5.6)."""
    mono_idx, rows = {(): 0}, []
    def midx(S):
        S = tuple(sorted(S))
        if S not in mono_idx: mono_idx[S] = len(mono_idx)
        return mono_idx[S]
    for H in homs:
        r = 1 << midx(())
        for size in (1, 2, 3):
            for S in itertools.combinations(H, size):
                r ^= 1 << midx(S)
        rows.append(r)
    basis, rank = {}, 0
    def reduce(v):
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: return v, p
        return 0, None
    for v in rows:
        v, p = reduce(v)
        if v: basis[p] = v; rank += 1
    one, _ = reduce(1 << midx(()))
    return rank, len(rows), one != 0   # independent iff rank==len; 1 not in span iff one!=0

#!/usr/bin/env python3
"""Deletion-filter extraction of minimal forcing families (Ch. 7 / Thm 4.20):
a subfamily F of lines is r-forcing iff the 'every line of F bichromatic' CNF
is unsatisfiable; the filter removes lines one at a time, keeping a removal
iff unsatisfiability survives. The result is minimal: for every kept line,
removal makes the instance satisfiable (checked)."""
from pysat.formula import CNF
from pysat.solvers import Solver

def cnf_of(lines, keep):
    cnf = CNF()
    for j in keep:
        L = lines[j]
        cnf.append([-(i + 1) for i in L]); cnf.append([(i + 1) for i in L])
    return cnf

def unsat(lines, keep, solver="cadical153"):
    with Solver(name=solver, bootstrap_with=cnf_of(lines, keep)) as s:
        return not s.solve()

def deletion_filter(lines, solver="cadical153"):
    assert unsat(lines, range(len(lines)), solver), "family is not forcing"
    keep = list(range(len(lines)))
    for j in list(keep):
        trial = [x for x in keep if x != j]
        if unsat(lines, trial, solver):
            keep = trial
    for j in keep:  # certify minimality
        assert not unsat(lines, [x for x in keep if x != j], solver)
    return keep

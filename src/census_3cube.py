#!/usr/bin/env python3
"""Censuses of [3]^3 (Appendix A.4): the line-free 2-colourings (Table A.5)
and the diagonal-only 2-colourings (Table A.6), with coordinate-stabilizer
strata. Exhaustive by depth-first search with line pruning."""
import itertools

WORDS = list(itertools.product((1, 2, 3), repeat=3))
IDX = {w: i for i, w in enumerate(WORDS)}

def lines():
    out = []
    for root in itertools.product((1, 2, 3, "*"), repeat=3):
        if "*" in root:
            out.append(tuple(IDX[tuple(a if a != "*" else s for a in root)] for s in (1, 2, 3)))
    return out

LINES = lines()
DIAG = tuple(IDX[(s, s, s)] for s in (1, 2, 3))

def _dfs(constraint):
    """Enumerate 2-colourings word-by-word; constraint(col, i) prunes."""
    by_last = [[] for _ in range(27)]
    for L in LINES:
        by_last[max(L)].append(L)
    col = [None] * 27
    out = []
    def rec(i):
        if i == 27:
            out.append(tuple(col)); return
        for c in (0, 1):
            col[i] = c
            if constraint(col, i, by_last[i]):
                rec(i + 1)
        col[i] = None
    rec(0)
    return out

def linefree():
    def ok(col, i, finished):
        return all(len({col[a] for a in L}) > 1 for L in finished)
    return _dfs(ok)

def diagonal_only():
    def ok(col, i, finished):
        for L in finished:
            mono = len({col[a] for a in L}) == 1
            if L == DIAG:
                if not mono: return False
            elif mono:
                return False
        return True
    return _dfs(ok)

PERMS = list(itertools.permutations(range(3)))
def stabilizer(col):
    stab = []
    for p in PERMS:
        if all(col[IDX[tuple(w[p[i]] for i in range(3))]] == col[IDX[w]] for w in WORDS):
            stab.append(p)
    return stab

def strata(cols):
    st = {"symmetric": 0, "C2": 0, "C3": 0, "trivial": 0}
    orbits = 0
    for col in cols:
        s = len(stabilizer(col))
        orbits += s
        st["symmetric" if s == 6 else "C3" if s == 3 else "C2" if s == 2 else "trivial"] += 1
    assert orbits % 6 == 0
    return st, orbits // 6

def sumtype_count(cols):
    target = set()
    for pal in itertools.product((0, 1), repeat=7):
        col = tuple(pal[sum(w) - 3] for w in WORDS)
        target.add(col)
    return sum(1 for c in cols if tuple(c) in target)

"""
geom_search.py -- decides HJ^geom(3,2) by exhaustion.

Enumerates the geometric lines of [3]^n from pm-roots and searches, by
plain backtracking over the colorings, for a 2-coloring of [3]^n with
no monochromatic geometric line.  No solver is involved.
"""
from itertools import product


def geom_lines(t, n):
    def point(tau, k):                # tau(k): A ascending, D descending
        return tuple(k if x == 'A' else (t + 1 - k if x == 'D' else x)
                     for x in tau)
    roots = product(list(range(1, t + 1)) + ['A', 'D'], repeat=n)
    return {frozenset(point(tau, k) for k in range(1, t + 1))
            for tau in roots if any(x in ('A', 'D') for x in tau)}


def avoiding_coloring(t, n):
    lines = [tuple(sorted(L)) for L in geom_lines(t, n)]
    pts = sorted({p for L in lines for p in L})
    idx = {p: i for i, p in enumerate(pts)}
    lines = [tuple(idx[p] for p in L) for L in lines]
    inc = [[] for _ in pts]
    for j, L in enumerate(lines):
        for p in L:
            inc[p].append(j)
    col = [None] * len(pts)

    def mono(j):
        v = {col[p] for p in lines[j]}
        return None not in v and len(v) == 1

    def bt(i):
        if i == len(pts):
            return True
        for c in (0, 1):
            col[i] = c
            if not any(mono(j) for j in inc[i]) and bt(i + 1):
                return True
        col[i] = None
        return False

    return dict(zip(pts, col)) if bt(0) else None


if __name__ == '__main__':
    for n in (2, 3):
        w = avoiding_coloring(3, n)
        m = len(geom_lines(3, n))
        print(f'n={n}: {m} geometric lines, '
              f'avoiding 2-coloring: {"yes" if w else "no"}')

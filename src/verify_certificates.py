"""
verify_certificates.py -- standalone, dependency-free verifier.

Usage:  python3 verify_certificates.py t n r K certificate_file

Checks that the certificate assigns every cell of T_n^(t) a color
in {0,...,r-1} and that no corner tuple C_{k,v} with 1 <= k <= K
is monochromatic.  Exit code 0 if and only if it is valid.
"""
import sys


def cells_of(t, n):
    if t == 1:
        return [(n,)]
    return [(a,) + rest
            for a in range(n + 1) for rest in cells_of(t - 1, n - a)]


def main(t, n, r, K, path):
    coloring = {}
    with open(path) as f:
        for ln in f:
            *u, j = map(int, ln.split())
            coloring[tuple(u)] = j
    assert set(coloring) == set(cells_of(t, n)), 'does not cover T_n'
    assert all(0 <= j < r for j in coloring.values()), 'bad color'
    bad = checked = 0
    for k in range(1, min(K, n) + 1):
        for v in cells_of(t, n - k):
            tup = [tuple(v[i] + (k if i == j else 0)
                         for i in range(t)) for j in range(t)]
            checked += 1
            if len({coloring[u] for u in tup}) == 1:
                bad += 1
    print(f'corner tuples checked: {checked}, monochromatic: {bad}')
    sys.exit(0 if bad == 0 else 1)


if __name__ == '__main__':
    t, n, r, K = map(int, sys.argv[1:5])
    main(t, n, r, K, sys.argv[5])

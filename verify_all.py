#!/usr/bin/env python3
"""
verify_all.py -- reproduce every avoidance certificate in this repository
by direct enumeration, independently of any SAT solver.

Run:  python3 verify_all.py

Exit code 0 iff all certificates pass. No third-party dependencies.
Each check re-derives the monochromatic-pattern condition from the
definitions in the thesis (Lemmas on the line--pattern and symmetric
reductions) and reports the number of forbidden patterns checked, so a
skipped pattern would show as a wrong count.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(HERE, "certificates")


def cells_of(t, n):
    """All types (a_1,...,a_t) with sum n, i.e. the simplex T_n^(t)."""
    if t == 1:
        return [(n,)]
    out = []

    def rec(prefix, rem, left):
        if left == 1:
            out.append(tuple(prefix + [rem]))
            return
        for x in range(rem + 1):
            rec(prefix + [x], rem - x, left - 1)

    rec([], n, t)
    return out


def check_simplex(coloring, t, n, r, K):
    """No corner tuple C_{k,v} (1<=k<=K) is monochromatic."""
    assert set(coloring) == set(cells_of(t, n)), "certificate does not cover T_n^(t)"
    assert all(0 <= j < r for j in coloring.values()), "colour out of range"
    bad = checked = 0
    for k in range(1, min(K, n) + 1):
        for v in cells_of(t, n - k):
            corner = [tuple(v[i] + (k if i == e else 0) for i in range(t))
                      for e in range(t)]
            checked += 1
            if len({coloring[u] for u in corner}) == 1:
                bad += 1
    return bad, checked


def load_cert(path):
    coloring = {}
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            *u, j = map(int, ln.split())
            coloring[tuple(u)] = j
    return coloring


def read_palette(path):
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                return [int(c) for c in ln]
    raise ValueError("no palette line in " + path)


def homothet_free(chi, S, kmax):
    """No monochromatic b + k*S inside the window, 1<=k<=kmax."""
    N = len(chi)
    D = max(S)
    bad = checked = 0
    for k in range(1, kmax + 1):
        for b in range(N - D * k):
            checked += 1
            if len({chi[b + k * s] for s in S}) == 1:
                bad += 1
    return bad, checked


def equation_free(chi):
    """No monochromatic injective solution of z + 2x = 3y in the window."""
    N = len(chi)
    bad = checked = 0
    for x in range(N):
        for y in range(N):
            z = 3 * y - 2 * x
            if 0 <= z < N and len({x, y, z}) == 3:
                checked += 1
                if chi[x] == chi[y] == chi[z]:
                    bad += 1
    return bad, checked


def periodic_ap_free(chi, t, kmax):
    """No monochromatic t-term AP of gap 1<=k<=kmax in Z/len(chi)."""
    m = len(chi)
    bad = checked = 0
    for k in range(1, kmax + 1):
        for b in range(m):
            checked += 1
            if len({chi[(b + i * k) % m] for i in range(t)}) == 1:
                bad += 1
    return bad, checked


def periodic_oneweight_free(chi, weight, t, n, kmax):
    """One-weight palette chi (m-periodic): no mono line of scale<=kmax on [t]^n."""
    m = len(chi)
    bad = checked = 0
    for k in range(1, kmax + 1):
        for v in cells_of(t, n - k):
            b = sum(weight[i] * v[i] for i in range(t)) % m
            checked += 1
            if len({chi[(b + k * weight[i]) % m] for i in range(t)}) == 1:
                bad += 1
    return bad, checked


def main():
    results = []

    def record(name, expect_checked, bad, checked):
        ok = (bad == 0) and (expect_checked is None or checked == expect_checked)
        results.append((name, ok, bad, checked))

    # HJ(3,3) >= 22
    c = load_cert(os.path.join(CERT, "hj33_ge22_T21.cert"))
    b, ck = check_simplex(c, 3, 21, 3, 21)
    record("HJ(3,3) >= 22   (T_21^(3), 1771 corner triples)", 1771, b, ck)

    # HJ(4,2) >= 14
    c = load_cert(os.path.join(CERT, "hj42_ge14_T13.cert"))
    b, ck = check_simplex(c, 4, 13, 2, 13)
    record("HJ(4,2) >= 14   (T_13^(4), 1820 corner quadruples)", 1820, b, ck)

    # G_3({0,2,5}) >= 77  =>  HJ(3,3) >= 16
    chi = read_palette(os.path.join(CERT, "hj33_interval76.txt"))
    b, ck = homothet_free(chi, [0, 2, 5], (len(chi) - 1) // 5)
    record("HJ(3,3) >= 16   ({0,2,5}-homothet-free window of 76)", None, b, ck)

    # G_4({0,1,3}) >= 94
    chi = read_palette(os.path.join(CERT, "gallai_013_window93.txt"))
    b, ck = homothet_free(chi, [0, 1, 3], (len(chi) - 1) // 3)
    record("G_4({0,1,3}) >= 94   ({0,1,3}-homothet-free window of 93)", None, b, ck)

    # R_4(z+2x=3y) >= 57
    chi = read_palette(os.path.join(CERT, "rado_z2x3y_len56.txt"))
    b, ck = equation_free(chi)
    record("R_4(z+2x=3y) >= 57   (solution-free window of 56)", None, b, ck)

    # kappa_sum(3,3) = 11
    chi = read_palette(os.path.join(CERT, "ksum33_period12.txt"))
    b, ck = periodic_ap_free(chi, 3, 11)
    record("kappa_sum(3,3) = 11   (period-12, no 3-AP of gap<=11)", None, b, ck)

    # HJ(3,3) >= 15 : 49-periodic one-weight palette, omega=(0,1,4), line-free on [3]^14
    chi = read_palette(os.path.join(CERT, "hj33_periodic49.txt"))
    b, ck = periodic_oneweight_free(chi, [0, 1, 4], 3, 14, 14)
    record("HJ(3,3) >= 15   (49-periodic one-weight palette on [3]^14)", None, b, ck)

    width = max(len(n) for n, *_ in results)
    print("=" * (width + 34))
    print("Direct-enumeration verification of all certificates")
    print("=" * (width + 34))
    allok = True
    for name, ok, bad, checked in results:
        tag = "PASS" if ok else "FAIL"
        allok &= ok
        print(f"[{tag}] {name.ljust(width)}  patterns={checked:>5} mono={bad}")
    print("=" * (width + 34))
    print("ALL CERTIFICATES VERIFIED" if allok else "SOME CERTIFICATES FAILED")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()

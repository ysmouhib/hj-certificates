#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_hj.py  --  standalone, dependency-free verifier for the two lower bounds

        HJ(3,3) >= 22        and        HJ(4,2) >= 14.

Run it with no arguments:

        python3 verify_hj.py

It needs nothing but the Python standard library, embeds both witness colorings
*byte-for-byte*, re-derives every combinatorial object from scratch, and prints
VERIFIED for each bound (exit code 0).  Nothing here depends on a SAT solver:
the solver only *found* the two colorings; their correctness is the finite
check performed below, which a patient reader could in principle redo by hand.

================================================================================
The mathematics being checked
================================================================================
Fix an alphabet [t] = {1,...,t} and a dimension n.  A *symmetric* r-coloring of
the grid [t]^n is one invariant under the S_n action permuting the n
coordinates.  Such a coloring depends only on the *type* of a word,

        type(w) = (a_1, ..., a_t),   a_j = number of coordinates of w equal to j,

so it is the same thing as a coloring of the discrete simplex of types

        T_n^(t) = { (a_1,...,a_t) : a_j >= 0,  a_1 + ... + a_t = n },
        |T_n^(t)| = C(n + t - 1, t - 1).                       (weak compositions)

A combinatorial line is given by a root with k >= 1 "active" (starred)
coordinates and a fixed part of type v in T_{n-k}^(t).  Setting the k stars to
the letter a contributes the inactive part (type v) plus k copies of a, so its
t points have exactly the types

        C_{k,v} = { v + k*e_1,  v + k*e_2,  ...,  v + k*e_t },     (the "corner tuple")

where e_j is the j-th standard basis vector.  Therefore, under a symmetric
coloring, that line is monochromatic IFF the coloring is constant on the t
cells of C_{k,v}.  Summing over all roots gives the exact equivalence

   symmetric coloring is line-free  <=>  no corner tuple C_{k,v}, 1 <= k <= n,
                                          is monochromatic.

If a line-free symmetric r-coloring of [t]^n exists, then [t]^n is not
"Ramsey" for r colors, so HJ(t,r) >= n + 1.  That is exactly what the two
embedded tables witness, with (t,n,r) = (3,21,3) and (4,13,2).

================================================================================
The number of objects checked (sanity targets)
================================================================================
   (3,3):  |T_21^(3)| = C(23,2) = 253 cells,   C(23,3) = 1771 corner triples.
   (4,2):  |T_13^(4)| = C(16,3) = 560 cells,   C(16,4) = 1820 corner quadruples.
"""

import argparse
import random
import sys
from math import comb


# =============================================================================
# 1.  The two witness tables, embedded verbatim (these are the published proofs)
# =============================================================================

# ---- HJ(3,3) >= 22 : a 3-coloring of T_21^(3) (the simplex of [3]^21) --------
#
# Layout: one row per value a = 0,1,...,21 (the number of 1's).  Row a is a
# string of length 22 - a; its character at position b (b = 0,1,...,21-a) is the
# colour of the cell (a, b, 21-a-b), i.e. the words with a ones, b twos and the
# rest threes.  253 characters in total.
WITNESS_HJ33 = """\
0102210210210210210022
121002102102102102210
20211021021021021102
2210121001102022210
002111211020021102
11022202100210021
2210102022021210
002120011211102
11020112202021
2210021102210
022111020102
01020110021
1210002211
202110102
01022021
1210210
202202
01101
1001
120
20
0
"""

# ---- HJ(4,2) >= 14 : a 2-coloring of T_13^(4) (the simplex of [4]^13) --------
#
# Layout: 14 "slices", one per value a = 0,...,13 (the number of 1's).  Inside
# slice a the whitespace-separated strings are indexed by b = 0,...,13-a (the
# number of 2's); the b-th string has length 14 - a - b and its character at
# position c (c = 0,...,13-a-b) is the colour of the cell (a, b, c, 13-a-b-c),
# i.e. a ones, b twos, c threes and the rest fours.  A slice may wrap over two
# physical lines; the parser simply concatenates the tokens of each slice.
# 560 characters in total.
WITNESS_HJ42 = """\
a= 0: 01111111000001 0101000110111 010001110101 00101010011
      0110011010 100110101 01101001 0101100 000110 11010 1010 100 00 0
a= 1: 1010101001011 000110101110 00111101000 1001000110
      010011110 00110001 0010111 010001 11000 0011 110 01 1
a= 2: 100110011011 11000110100 1010100101 111001000
      01011001 1001011 110110 00110 0010 001 01 0
a= 3: 01010001111 0101111000 101100001 10001111 1110000 001011 10100 1001 111 10 0
a= 4: 1001010011 011001010 10011010 0100111 100110 01100 1001 001 01 1
a= 5: 000110110 11000100 0010111 111000 00011 1100 011 10 1
a= 6: 00100110 1001000 011001 10101 0101 010 11 1
a= 7: 1110000 001010 01010 0101 101 11 0
a= 8: 101101 10001 0100 011 10 0
a= 9: 11001 0011 110 00 1
a=10: 1100 111 10 0
a=11: 000 01 1
a=12: 11 1
a=13: 0
"""


# =============================================================================
# 2.  Core combinatorics, re-derived from scratch
# =============================================================================

def simplex_cells(t, n):
    """Yield every type in T_n^(t): all weak compositions of n into t parts.

    A weak composition is a t-tuple of non-negative integers summing to n.  We
    build them recursively: choose the first part 'first' in 0..n, then recurse
    to split the remaining n-first over the other t-1 parts.  The number of
    tuples produced is C(n+t-1, t-1).
    """
    if t == 1:
        yield (n,)
        return
    for first in range(n + 1):
        for rest in simplex_cells(t - 1, n - first):
            yield (first,) + rest


def corner_tuples(t, n, kmax):
    """Yield (k, v, cells) for every corner tuple C_{k,v} with 1 <= k <= kmax.

    For each step size k and each inactive type v in T_{n-k}^(t), the tuple is
    the t cells  v + k*e_1, ..., v + k*e_t  (add k to one coordinate at a time).
    The total number produced for kmax = n is C(n+t-1, t) (hockey-stick identity).
    """
    for k in range(1, kmax + 1):
        for v in simplex_cells(t, n - k):
            cells = tuple(
                tuple(v[i] + (k if i == j else 0) for i in range(t))
                for j in range(t)
            )
            yield k, v, cells


def main_diagonal(t, n):
    """The single corner tuple with k = n: the t pure-letter cells {n*e_j}."""
    return tuple(tuple(n if i == j else 0 for i in range(t)) for j in range(t))


# =============================================================================
# 3.  Parsers turning the embedded strings into a coloring dict {cell: colour}
# =============================================================================

def parse_triangle(text, n):
    """Parse the t = 3 table (one string per row a; see WITNESS_HJ33 above).

    Returns a dict mapping each cell (a, b, c) with a+b+c = n to its colour.
    Each row a must have exactly n+1-a characters (cells with c = n-a-b >= 0).
    """
    coloring = {}
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if len(rows) != n + 1:
        raise ValueError(f"expected {n+1} rows, found {len(rows)}")
    for a, row in enumerate(rows):
        if len(row) != n + 1 - a:
            raise ValueError(f"row a={a}: length {len(row)} != {n+1-a}")
        for b, ch in enumerate(row):
            c = n - a - b
            coloring[(a, b, c)] = int(ch)
    return coloring


def parse_slices(text, n):
    """Parse the t = 4 table (slices over a, strings over b; see WITNESS_HJ42).

    Returns a dict mapping each cell (a, b, c, d) with a+b+c+d = n to its colour.
    Lines beginning with 'a=' open a new slice; any following continuation lines
    contribute more tokens to the current slice.  Within slice a there must be
    n+1-a tokens (b = 0..n-a) and the b-th token must have length n+1-a-b.
    """
    slices = {}
    current = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("a="):
            head, _, rest = line.partition(":")
            current = int(head.split("=")[1])
            slices[current] = rest.split()
        else:
            if current is None:
                raise ValueError("continuation line before any 'a=' header")
            slices[current].extend(line.split())

    coloring = {}
    if len(slices) != n + 1:
        raise ValueError(f"expected {n+1} slices, found {len(slices)}")
    for a, tokens in slices.items():
        if len(tokens) != n + 1 - a:
            raise ValueError(f"slice a={a}: {len(tokens)} tokens != {n+1-a}")
        for b, token in enumerate(tokens):
            if len(token) != n + 1 - a - b:
                raise ValueError(f"a={a}, b={b}: length {len(token)} != {n+1-a-b}")
            for c, ch in enumerate(token):
                d = n - a - b - c
                coloring[(a, b, c, d)] = int(ch)
    return coloring


# =============================================================================
# 4.  The verification itself
# =============================================================================

def verify_symmetric(coloring, t, n, r):
    """Check that 'coloring' is a line-free symmetric r-coloring of [t]^n.

    Three independent checks:
      (a) totality   -- the colored cells are exactly the simplex T_n^(t);
      (b) range      -- every colour lies in {0, ..., r-1};
      (c) line-free  -- no corner tuple C_{k,v} (1 <= k <= n) is monochromatic.
    Returns a report dict; report['ok'] is True iff all checks pass.
    """
    report = {"ok": True, "errors": []}

    # (a) totality: the cell set must equal the full simplex, no more, no less.
    expected = set(simplex_cells(t, n))
    got = set(coloring)
    if got != expected:
        report["ok"] = False
        report["errors"].append(
            f"cell-set mismatch: missing {len(expected - got)}, extra {len(got - expected)}"
        )

    # (b) colours in range.
    out_of_range = [(cell, col) for cell, col in coloring.items() if not (0 <= col < r)]
    if out_of_range:
        report["ok"] = False
        report["errors"].append(f"{len(out_of_range)} cell(s) with colour outside 0..{r-1}")

    # (c) the heart of the proof: scan every corner tuple for monochromaticity.
    checked = 0
    mono = []
    for k, v, cells in corner_tuples(t, n, n):
        checked += 1
        if len({coloring[u] for u in cells}) == 1:   # all t cells share a colour
            mono.append((k, v))
    report["corner_tuples_checked"] = checked
    report["monochromatic_tuples"] = len(mono)
    if mono:
        report["ok"] = False
        report["errors"].append(f"{len(mono)} monochromatic corner tuple(s), e.g. {mono[:3]}")

    # informational: the status of the main diagonal (k = n).
    diag = main_diagonal(t, n)
    report["cells"] = len(coloring)
    report["diagonal_cells"] = diag
    report["diagonal_colors"] = [coloring[u] for u in diag]
    return report


def sample_grid_lines(coloring, t, n, samples, seed=0):
    """Independent cross-check directly on the full grid [t]^n (no reduction).

    We draw random roots (each coordinate is a star with probability 1/(t+1),
    else a fixed letter), force at least one star, build the t words of the
    line, recompute each word's type by *counting letters from scratch*, look up
    its colour, and confirm the t colours are not all equal.  This exercises the
    symmetric lift end-to-end and so guards against a bug in the reduction logic
    of verify_symmetric.  It is a sanity check, not part of the proof.

    Returns (samples_done, monochromatic_found).
    """
    rng = random.Random(seed)
    mono_found = 0
    for _ in range(samples):
        # draw a root: -1 marks an active (starred) coordinate.
        root = [rng.randrange(-1, t) for _ in range(n)]
        if -1 not in root:
            root[rng.randrange(n)] = -1          # guarantee at least one star
        colors = set()
        for a in range(t):                       # the t words of this line
            counts = [0] * t
            for x in root:
                counts[a if x == -1 else x] += 1  # stars take letter a
            colors.add(coloring[tuple(counts)])
        if len(colors) == 1:
            mono_found += 1
    return samples, mono_found


# =============================================================================
# 5.  Drivers and command-line interface
# =============================================================================

def run_case(name, witness_text, parser, t, n, r, bound, samples):
    """Parse one witness, verify it, optionally sample the grid, and report."""
    print(f"=== {name}:  HJ({t},{r}) >= {bound}  "
          f"(line-free symmetric {r}-coloring of [{t}]^{n}) ===")
    try:
        coloring = parser(witness_text, n)
    except (ValueError, KeyError) as exc:
        # A malformed table is reported here rather than as a raw traceback.
        print(f"  RESULT: FAILED  (could not parse the embedded table: {exc})\n")
        return False

    exp_cells = comb(n + t - 1, t - 1)
    exp_tuples = comb(n + t - 1, t)
    print(f"  cells in T_{n}^({t})      : {len(coloring)}  (expected C({n+t-1},{t-1}) = {exp_cells})")

    report = verify_symmetric(coloring, t, n, r)
    print(f"  corner tuples checked  : {report['corner_tuples_checked']}  "
          f"(expected C({n+t-1},{t}) = {exp_tuples})")
    print(f"  monochromatic tuples   : {report['monochromatic_tuples']}")
    print(f"  main diagonal (k={n}) cells colored {report['diagonal_colors']}  "
          f"-> {'NOT ' if len(set(report['diagonal_colors'])) > 1 else ''}monochromatic")

    if samples > 0:
        done, mono = sample_grid_lines(coloring, t, n, samples)
        print(f"  random grid lines      : {done} sampled, {mono} monochromatic "
              f"(independent cross-check)")
        if mono:
            report["ok"] = False
            report["errors"].append(f"sampling found {mono} monochromatic line(s)")

    if report["ok"]:
        print(f"  RESULT: VERIFIED  =>  HJ({t},{r}) >= {bound}\n")
    else:
        print("  RESULT: FAILED")
        for e in report["errors"]:
            print(f"    - {e}")
        print()
    return report["ok"]


def main():
    ap = argparse.ArgumentParser(
        description="Dependency-free verifier for HJ(3,3) >= 22 and HJ(4,2) >= 14."
    )
    ap.add_argument("--only", choices=["33", "42"], default=None,
                    help="verify only the (3,3) or the (4,2) bound (default: both)")
    ap.add_argument("--sample", type=int, default=200000,
                    help="random grid lines to cross-check per case (0 to skip; "
                         "default 200000)")
    args = ap.parse_args()

    ok = True
    if args.only in (None, "33"):
        ok &= run_case("HJ(3,3)", WITNESS_HJ33, parse_triangle,
                       t=3, n=21, r=3, bound=22, samples=args.sample)
    if args.only in (None, "42"):
        ok &= run_case("HJ(4,2)", WITNESS_HJ42, parse_slices,
                       t=4, n=13, r=2, bound=14, samples=args.sample)

    print("ALL CHECKS PASSED." if ok else "SOME CHECK FAILED.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
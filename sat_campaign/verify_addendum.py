#!/usr/bin/env python3
"""Independent verification of every certificate in results.json:
for each recorded SAT entry, re-checks by brute force that the coloring
avoids all homothets of its shape(s); prints the final threshold table.
Pure standard library.  Run: python3 verify_addendum.py"""

import json, sys
sys.path.insert(0, '.')
from gallai_rado_sat import homothets, verify_coloring

res = json.load(open('results.json'))
fails = 0
rows = []
for key, inst in sorted(res.items()):
    shapes = [tuple(map(int, s.split(','))) for s in key.split(':')[0].split('|')]
    r = int(key.split(':r')[1])
    sat_ns = sorted(int(n) for n, v in inst.items() if v['status'] == 'SAT')
    unsat_ns = sorted(int(n) for n, v in inst.items() if v['status'] == 'UNSAT')
    lo = max(sat_ns) if sat_ns else None
    hi = min(unsat_ns) if unsat_ns else None
    # re-verify every recorded avoidance coloring independently
    for n in sat_ns:
        col = [int(x) for x in inst[str(n)]['coloring']]
        ok = len(col) == n and verify_coloring(shapes, r, col)
        if not ok:
            print(f"FAIL  {key} N={n}: coloring does NOT avoid shapes")
            fails += 1
    exact = (lo is not None and hi == lo + 1)
    rows.append((key, lo, hi, exact))

w = max(len(k) for k, _, _, _ in rows)
print(f"{'instance':<{w}}  avoidance  forcing  status")
for key, lo, hi, exact in rows:
    st = ('EXACT: value = ' + str(hi)) if exact else ('gap: > %d, <= %s' %
          (lo, hi if hi is not None else '?'))
    print(f"{key:<{w}}  N={lo:<8} N={hi!s:<7} {st}")
print('\n' + ('ALL ADDENDUM CERTIFICATES VERIFIED' if fails == 0
              else f'{fails} FAILURE(S)'))

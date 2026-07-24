#!/usr/bin/env python3
"""Independent re-refutation of the paper's forcing claims.
Clean-room encoder (written from the definitions in the paper, not from the
shipped gallai_rado_sat.py); pysat Cadical195 backend; optional DIMACS dump."""
import sys, time, json

def homs(shapes, N):
    out = set()
    for S in shapes:
        m = max(S)
        for k in range(1, (N - 1) // m + 1):
            for b in range(N - k * m):
                out.add(tuple(b + k * s for s in S))
    return sorted(out)

def encode(shapes, r, N, symbreak=True):
    v = lambda c, i: c * r + i + 1
    cls = []
    for c in range(N):
        cls.append([v(c, i) for i in range(r)])
        for i in range(r):
            for j in range(i + 1, r):
                cls.append([-v(c, i), -v(c, j)])
    for H in homs(shapes, N):
        for i in range(r):
            cls.append([-v(c, i) for c in H])
    if symbreak:
        for i in range(r):
            for j in range(i + 1, r):
                for c in range(N):
                    cls.append([-v(c, j)] + [v(cc, i) for cc in range(c)])
    return cls, N * r

def run(shapes, r, N, expect, symbreak=True):
    from pysat.solvers import Cadical195
    cls, nv = encode(shapes, r, N, symbreak)
    t0 = time.time()
    with Cadical195(bootstrap_with=cls) as s:
        sat = s.solve()
    dt = time.time() - t0
    verdict = "SAT" if sat else "UNSAT"
    flag = "OK " if verdict == expect else "MISMATCH"
    print(f"{flag} {shapes} r={r} N={N}: {verdict} ({dt:.1f}s, "
          f"{len(cls)} clauses)", flush=True)
    return verdict == expect

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "dimacs":
        shapes = [tuple(map(int, s.split(","))) for s in sys.argv[2].split("|")]
        r, N = int(sys.argv[3]), int(sys.argv[4])
        sb = (len(sys.argv) < 6 or sys.argv[5] != "nosym")
        cls, nv = encode(shapes, r, N, sb)
        with open(sys.argv[6] if len(sys.argv) > 6 else "inst.cnf", "w") as f:
            f.write(f"p cnf {nv} {len(cls)}\n")
            for c in cls:
                f.write(" ".join(map(str, c)) + " 0\n")
        print(f"wrote {len(cls)} clauses, {nv} vars (symbreak={sb})")
    elif mode == "batch":
        G2 = {(0,1,2,4):38,(0,1,3,4):41,(0,2,4,5):44,(0,3,4,5):44,(0,1,4,5):45,
              (0,1,3,6):52,(0,2,3,6):54,(0,1,2,6):56,(0,1,4,6):58,(0,1,2,7):59,
              (0,2,5,7):59,(0,1,3,7):60,(0,2,4,7):61,(0,1,4,7):62,(0,1,5,7):62,
              (0,2,3,7):62,(0,1,6,7):79,(0,3,4,7):79}
        ok = True
        for S, g in sorted(G2.items()):
            ok &= run([S], 2, g, "UNSAT")
            ok &= run([S], 2, g - 1, "SAT")
        for S, r, g in [((0,1,2),2,9),((0,1,3),2,13),((0,1,2),3,27),
                        ((0,1,3),3,42),((0,1,4),3,57),((0,1,5),3,70)]:
            ok &= run([S], r, g, "UNSAT")
            ok &= run([S], r, g - 1, "SAT")
        RAD = {(2,2):13,(3,2):17,(4,2):19,(5,2):25,
               (2,3):29,(3,3):54,(4,3):55,(5,3):60}
        for (k, r), g in sorted(RAD.items()):
            sh = [(0,1,k+1),(0,k,k+1)]
            ok &= run(sh, r, g, "UNSAT")
            ok &= run(sh, r, g - 1, "SAT")
        print("BATCH:", "ALL OK" if ok else "MISMATCHES PRESENT")
    elif mode == "flag":
        run([(0,2,5)], 3, 77, "UNSAT")

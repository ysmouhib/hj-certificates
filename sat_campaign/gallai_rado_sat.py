#!/usr/bin/env python3
"""Gallai-Rado SAT engine: computes homothety-avoidance (Gallai) and
solution-freeness (Rado) thresholds with a portfolio of state-of-the-art
SAT solvers.

For shapes S_1, ..., S_m (integer tuples containing 0) and r colors, the
engine determines, for intervals [0, N-1], whether some r-coloring avoids
a monochromatic homothet of every S_i (avoidance / lower bound), or whether
every r-coloring contains one (forcing / upper bound, UNSAT).

  G_r(S)   = least N such that forcing holds on [0, N-1]  (m = 1)
  R_r(E_k) = Rado number of z + kx = (k+1)y: solutions are exactly the
             homothets of {0,1,k+1} and of {0,k,k+1}, so m = 2.

Methods: one-hot CNF encoding + complete color-permutation symmetry
breaking (first-occurrence ordering), a solver portfolio race
(Kissat, CaDiCaL, CryptoMiniSat, Glucose, MapleSAT, Lingeling via PySAT),
and a domain-specific stochastic local search (min-conflicts with random
walk) for the avoidance side near the threshold.  Every SAT-found
coloring is re-verified by brute force before being recorded.

Usage:
  python3 gallai_rado_sat.py scan  -s 0,1,5 -r 3 [--nmax 200] [--budget 120]
  python3 gallai_rado_sat.py rado  -k 2 -r 4 [--nmax 200] [--budget 120]
  python3 gallai_rado_sat.py check -s 0,1,5 -r 3 -c 0012...
Requires: pip install python-sat
"""

import argparse, json, os, sys, time
from multiprocessing import Process, Queue

# persistent local install of python-sat / pycryptosat (home dir is ephemeral)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'pylibs'))

# ---------------------------------------------------------------- encoding --
def homothets(shapes, N):
    """All homothets {b + k*a : a in S} inside [0, N-1], k >= 1, b >= 0."""
    out = set()
    for S in shapes:
        amax = max(S)
        for k in range(1, N):
            for b in range(N - k * amax):
                out.add(tuple(b + k * a for a in S))
    return sorted(out)

def encode(shapes, r, N, symbreak=True):
    """One-hot CNF.  var (c, i) <-> cell c has color i."""
    hyps = homothets(shapes, N)
    var, nxt = {}, 0
    for c in range(N):
        for i in range(r):
            nxt += 1
            var[(c, i)] = nxt
    clauses = []
    for c in range(N):                                  # at least one color
        clauses.append([var[(c, i)] for i in range(r)])
        for i in range(r):                              # at most one color
            for j in range(i + 1, r):
                clauses.append([-var[(c, i)], -var[(c, j)]])
    for H in hyps:                                      # no mono homothet
        for i in range(r):
            clauses.append([-var[(c, i)] for c in H])
    if symbreak and r > 1:
        # first occurrence of color j not before first occurrence of color i<j
        for i in range(r):
            for j in range(i + 1, r):
                for c in range(N):
                    clauses.append([-var[(c, j)]] +
                                   [var[(cc, i)] for cc in range(c)])
    return clauses, var, hyps

def verify_coloring(shapes, r, col):
    """Brute-force check that coloring `col` of [0, N-1] avoids all shapes."""
    N = len(col)
    if any(not (0 <= x < r) for x in col):
        return False
    return all(len({col[c] for c in H}) > 1 for H in homothets(shapes, N))

# ------------------------------------------------------ stochastic search --
def sls_avoid(shapes, r, N, max_steps=200000, restarts=20, seed=1):
    """Min-conflicts with random walk on colorings; returns coloring or None."""
    import random
    rng = random.Random(seed)
    hyps = homothets(shapes, N)
    cell_hyps = [[] for _ in range(N)]
    for hi, H in enumerate(hyps):
        for c in H:
            cell_hyps[c].append(hi)
    for _ in range(restarts):
        col = [rng.randrange(r) for _ in range(N)]
        cnt = [[0] * r for _ in range(len(hyps))]       # color counts/homothet
        for hi, H in enumerate(hyps):
            for c in H:
                cnt[hi][col[c]] += 1
        mono_l = [hi for hi, H in enumerate(hyps) if len(H) in cnt[hi]]
        pos = {hi: i for i, hi in enumerate(mono_l)}
        def setmono(hi, ismono):
            if ismono and hi not in pos:
                pos[hi] = len(mono_l)
                mono_l.append(hi)
            elif not ismono and hi in pos:
                j = pos.pop(hi)
                last = mono_l.pop()
                if j < len(mono_l):
                    mono_l[j] = last
                    pos[last] = j
        for _step in range(max_steps):
            if not mono_l:
                return col
            hi = mono_l[rng.randrange(len(mono_l))]
            c = rng.choice(hyps[hi])
            old = col[c]
            # min-conflicts: choose the new color minimizing mono homothets
            best, new = None, None
            for cand in range(r):
                if cand == old:
                    continue
                gain = 0
                for hj in cell_hyps[c]:
                    gain += (cnt[hj][cand] + 1 == len(hyps[hj]))
                    gain -= (cnt[hj][old] == len(hyps[hj]))
                if best is None or gain < best:
                    best, new = gain, cand
            if best > 0 and rng.random() < 0.5:          # random walk
                new = rng.choice([x for x in range(r) if x != old])
            for hj in cell_hyps[c]:
                setmono(hj, False)
                cnt[hj][old] -= 1
                cnt[hj][new] += 1
                if cnt[hj][new] == len(hyps[hj]):
                    setmono(hj, True)
            col[c] = new
    return None

# ------------------------------------------------------------ solver race --
def _worker(shapes, r, N, solver, symbreak, q):
    try:
        clauses, var, hyps = encode(shapes, r, N, symbreak)
        t0 = time.time()
        if solver == "pycms":                             # CryptoMiniSat direct
            import pycryptosat
            s = pycryptosat.Solver()
            for cl in clauses:
                s.add_clause(cl)
            sat = bool(s.solve()[0])
            dt = time.time() - t0
            if sat:
                m = s.get_model()
                col = [next(i for i in range(r) if m[var[(c, i)]])
                       for c in range(N)]
                q.put(dict(solver=solver, status="SAT", coloring=col,
                           time=dt, nhyps=len(hyps)))
            else:
                q.put(dict(solver=solver, status="UNSAT", coloring=None,
                           time=dt, nhyps=len(hyps)))
            return
        from pysat.solvers import Solver
        with Solver(name=solver, bootstrap_with=clauses) as s:
            sat = s.solve()
            dt = time.time() - t0
            if sat:
                m = s.get_model()
                col = [next(i for i in range(r) if m[var[(c, i)] - 1] > 0)
                       for c in range(N)]
                q.put(dict(solver=solver, status="SAT", coloring=col,
                           time=dt, nhyps=len(hyps)))
            else:
                q.put(dict(solver=solver, status="UNSAT", coloring=None,
                           time=dt, nhyps=len(hyps)))
    except Exception as e:                                # solver unavailable
        q.put(dict(solver=solver, status="ERROR", error=str(e)))

def solve(shapes, r, N, solvers, budget, symbreak=True, use_sls=True):
    """Race `solvers` in parallel (2 at a time); SLS first for avoidance."""
    if use_sls:
        t0 = time.time()
        col = sls_avoid(shapes, r, N)
        if col is not None and verify_coloring(shapes, r, col):
            return dict(solver="sls", status="SAT", coloring=col,
                        time=time.time() - t0,
                        nhyps=len(homothets(shapes, N)))
    i = 0
    while i < len(solvers):
        group = solvers[i:i + 2]
        q = Queue()
        procs = [Process(target=_worker, args=(shapes, r, N, s, symbreak, q))
                 for s in group]
        for p in procs:
            p.start()
        t0 = time.time()
        result = None
        while time.time() - t0 < budget:
            try:
                result = q.get(timeout=1.0)
                if result["status"] == "ERROR":
                    print(f"  [{group}] {result['solver']} error: "
                          f"{result['error']}", flush=True)
                    result = None
                    continue
                break
            except Exception:
                if not any(p.is_alive() for p in procs):
                    break
        for p in procs:
            if p.is_alive():
                p.terminate()
            p.join()
        if result is not None:
            if result["status"] == "SAT":
                ok = verify_coloring(shapes, r, result["coloring"])
                assert ok, "solver produced an invalid coloring!"
            return result
        i += 2
    return dict(solver=None, status="UNKNOWN", coloring=None, time=budget,
                nhyps=len(homothets(shapes, N)))

# ------------------------------------------------------------------ driver --
def scan(shapes, r, nmin, nmax, budget, solvers, results_path):
    """Scan N upward; record avoidance/forcing status for each N."""
    results = {}
    if os.path.exists(results_path):
        results = json.load(open(results_path))
    key = "|".join(",".join(map(str, S)) for S in shapes) + f":r{r}"
    inst = results.setdefault(key, {})
    lower = upper = None
    for N in range(nmin, nmax + 1):
        if str(N) in inst:
            st = inst[str(N)]["status"]
            if st == "SAT":
                lower = N
            elif st == "UNSAT":
                upper = N
                break
            continue
        res = solve(shapes, r, N, solvers, budget)
        print(f"N={N:4d}  {res['status']:7s}  solver={res['solver']}  "
              f"{res['time']:.1f}s  homothets={res['nhyps']}", flush=True)
        if res["status"] == "UNKNOWN":
            break                       # not recorded: retried on resume
        rec = dict(status=res["status"], solver=res["solver"],
                   time=round(res["time"], 2), nhyps=res["nhyps"])
        if res["status"] == "SAT":
            rec["coloring"] = "".join(map(str, res["coloring"]))
            lower = N
        elif res["status"] == "UNSAT":
            upper = N
        inst[str(N)] = rec
        json.dump(results, open(results_path, "w"), indent=1)
        if res["status"] == "UNSAT":
            break
    print(f"==> {key}: avoidance up to N={lower}, forcing from N={upper}",
          flush=True)
    return key

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "rado"):
        p = sub.add_parser(name)
        if name == "scan":
            p.add_argument("-s", "--shape", required=True,
                           help="comma-separated, e.g. 0,1,5")
        else:
            p.add_argument("-k", type=int, required=True,
                           help="equation z + kx = (k+1)y")
        p.add_argument("-r", "--colors", type=int, required=True)
        p.add_argument("--nmin", type=int, default=1)
        p.add_argument("--nmax", type=int, default=200)
        p.add_argument("--budget", type=int, default=120,
                           help="seconds per solver group per N")
        p.add_argument("--solvers", default="kissat404,cadical195,pycms,"
                                            "glucose4,maplechrono,lingeling")
        p.add_argument("--results", default="results.json")
    p = sub.add_parser("check")
    p.add_argument("-s", "--shape", required=True)
    p.add_argument("-r", "--colors", type=int, required=True)
    p.add_argument("-c", "--coloring", required=True)
    args = ap.parse_args()

    if args.cmd == "check":
        S = tuple(map(int, args.shape.split(",")))
        col = [int(x) for x in args.coloring]
        ok = verify_coloring([S], args.colors, col)
        print("VALID avoidance coloring" if ok else "INVALID", flush=True)
        return

    shapes = ([tuple(map(int, args.shape.split(",")))] if args.cmd == "scan"
              else [(0, 1, args.k + 1), (0, args.k, args.k + 1)])
    solvers = [s for s in args.solvers.split(",") if s]
    scan(shapes, args.colors, args.nmin, args.nmax, args.budget, solvers,
         args.results)

if __name__ == "__main__":
    main()

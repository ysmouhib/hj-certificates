#!/usr/bin/env python3
"""
verify_all.py -- reproduce every avoidance certificate and every finite data
claim in this repository by direct enumeration, independently of any SAT
solver.

Run:  python3 verify_all.py

Exit code 0 iff all checks pass. No third-party dependencies (stdlib only).
Each check re-derives the forbidden-pattern condition from the definitions in
the thesis (the line--pattern correspondence, Lemma 2.14, and the symmetric
reduction, Lemma 3.1) and reports the number of patterns checked, so a skipped
pattern would show as a wrong count.  Forcing (unsatisfiability) claims are
NOT re-proved here -- they rest on the SAT runs recorded in logs/ -- but their
finite consequences (sharpness, counts, boundaries) are.
"""
import itertools, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(HERE, "certificates")
DATA = os.path.join(HERE, "data")
FAIL = []

def report(ok, label, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {label:<58} {detail}")
    if not ok: FAIL.append(label)

# ---------- shared helpers ----------
def cells(t, n):
    if t == 1: return [(n,)]
    return [(x,) + r for x in range(n + 1) for r in cells(t - 1, n - x)]

def read_palette(path):
    for ln in open(path):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            return [int(c) for c in ln]
    raise ValueError(path)

def read_cert(path):
    col = {}
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        *u, j = map(int, ln.split())
        col[tuple(u)] = j
    return col

def read_grid(path, n):
    col = {}
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        a = list(map(int, ln.split()))
        col[tuple(a[:n])] = a[n]
    return col

def corner_mono(t, n, colf, K=None):
    bad = chk = 0
    for k in range(1, (K or n) + 1):
        for v in cells(t, n - k):
            corner = [tuple(v[i] + (k if i == e else 0) for i in range(t)) for e in range(t)]
            chk += 1
            if len({colf(u) for u in corner}) == 1: bad += 1
    return bad, chk

def homothet_mono(chi, S, N=None):
    N = N or len(chi); D = max(S); bad = chk = 0
    k = 1
    while k * D <= N - 1:
        for b in range(N - k * D):
            chk += 1
            if len({chi[b + k * s] for s in S}) == 1: bad += 1
        k += 1
    return bad, chk

def grid_lines(t, n):
    words = list(itertools.product(range(1, t + 1), repeat=n))
    L = []
    for root in itertools.product(list(range(1, t + 1)) + ["*"], repeat=n):
        if "*" in root:
            L.append([tuple(a if a != "*" else s for a in root) for s in range(1, t + 1)])
    return words, L

# ---------- 1-2: the simplex records ----------
c = read_cert(os.path.join(CERT, "hj33_ge22_T21.cert"))
assert set(c) == set(cells(3, 21))
bad, chk = corner_mono(3, 21, c.__getitem__)
report(bad == 0 and chk == 1771, "HJ(3,3) >= 22   (T_21^(3))", f"corner triples={chk} mono={bad}")

c14 = read_cert(os.path.join(CERT, "hj42_ge14_T13.cert"))
assert set(c14) == set(cells(4, 13))
bad, chk = corner_mono(4, 13, c14.__getitem__)
report(bad == 0 and chk == 1820, "HJ(4,2) >= 14   (T_13^(4))", f"corner quadruples={chk} mono={bad}")

# ---------- 3: the period-26 record palette: equality, sharpness, anatomy ----------
chi26 = read_palette(os.path.join(CERT, "hj42_palette26.txt")); om = (0, 2, 3, 5)
lvl = lambda u: chi26[sum(o * x for o, x in zip(om, u)) % 26]
same = all(lvl(u) == c14[u] for u in c14)
b13, _ = corner_mono(4, 13, lvl)
b14, _ = corner_mono(4, 14, lvl)
ok12 = all(len({chi26[(b + o * k) % 26] for o in om}) > 1 for k in range(1, 13) for b in range(26))
surv = [b for b in range(26) if len({chi26[(b + o * 13) % 26] for o in om}) > 1]
report(same and b13 == 0 and b14 == 3 and ok12 and surv == [0, 13],
       "period-26 palette: record, sharpness, anatomy (Prop 5.3)",
       f"==T13 cert:{same} mono(n=13)={b13} mono(n=14)={b14} k<=12 clean:{ok12} k=13 survivors={surv}")

# ---------- 4-8: windows and periodic palettes already in v1 ----------
for fname, S, r, label, expect in [
        ("hj33_interval76.txt", (0, 2, 5), 3, "HJ(3,3) >= 16   (G_3({0,2,5}) >= 77)", 540),
        ("gallai_013_window93.txt", (0, 1, 3), 4, "G_4({0,1,3}) >= 94", 1395),
        ("gallai_013_r3_window41.txt", (0, 1, 3), 3, "G_3({0,1,3}) = 42   (window of 41; forcing: logs/)", 260),
        ("gallai_014_r3_window56.txt", (0, 1, 4), 3, "G_3({0,1,4}) = 57   (window of 56; forcing: logs/)", 364),
        ("gallai_0235_r2_window66.txt", (0, 2, 3, 5), 2, "G_2({0,2,3,5}) = 67 (window of 66; forcing: logs/)", 403),
        ("gallai_0156_r2_window79.txt", (0, 1, 5, 6), 2, "G_2({0,1,5,6}) = 80 (window of 79; forcing: logs/)", 481)]:
    chi = read_palette(os.path.join(CERT, fname))
    assert max(chi) < r
    bad, chk = homothet_mono(chi, S)
    report(bad == 0 and chk == expect, label, f"homothets={chk} mono={bad}")

chi = read_palette(os.path.join(CERT, "rado_z2x3y_len56.txt"))
b1, k1 = homothet_mono(chi, (0, 1, 3)); b2, k2 = homothet_mono(chi, (0, 2, 3))
report(b1 == 0 and b2 == 0 and len(chi) == 56,
       "R_4(z+2x=3y) >= 57  (free of {0,1,3} AND {0,2,3} copies)",
       f"injective solutions={k1 + k2} mono={b1 + b2}")

chi = read_palette(os.path.join(CERT, "ksum33_period12.txt"))
bad = sum(1 for b in range(12) for k in range(1, 12)
          if len({chi[(b + i * k) % 12] for i in range(3)}) == 1)
report(bad == 0, "kappa_sum(3,3) = 11 (period 12; forcing at 27: logs/)", f"pairs=132 mono={bad}")

chi = read_palette(os.path.join(CERT, "hj33_periodic49.txt")); omB = (0, 1, 4)
bad, chk = corner_mono(3, 14, lambda u: chi[sum(o * x for o, x in zip(omB, u)) % 49])
report(bad == 0 and chk == 560, "HJ(3,3) >= 15   (49-periodic palette on [3]^14)", f"corner triples={chk} mono={bad}")

# ---------- 9: the fourteen primitive classes (Prop 2.21) ----------
CL = [(1,1,9),(1,2,13),(1,3,17),(1,4,20),(2,3,21),(1,5,25),(1,6,29),(2,5,29),
      (3,4,29),(1,7,33),(3,5,33),(1,8,36),(2,7,37),(4,5,37)]
allok, tot = True, 0
for s, u, G in CL:
    D = s + u
    formula = 4 * D if (min(s, u) == 1 and max(s, u) % 4 == 0) else 4 * D + 1
    chi = read_palette(os.path.join(CERT, "gallai_D_le9_r2", f"g2_s{s}u{u}_window{G-1}.txt"))
    bad, chk = homothet_mono(chi, (0, s, s + u)); tot += chk
    allok &= (bad == 0 and len(chi) == G - 1 and formula == G and max(chi) < 2)
report(allok, "Prop 2.21: 14 primitive classes D<=9 match the formula",
       f"windows verified=14 homothets={tot} (exceptional: {{1,4}}->20, {{1,8}}->36)")

# ---------- 10: kappa_sum(4,3) = 96 ----------
p = read_palette(os.path.join(CERT, "ksum43_period97.txt")); assert len(p) == 97
bad = sum(1 for b in range(97) for k in range(1, 97)
          if len({p[(b + i * k) % 97] for i in range(4)}) == 1)
ind, x = {}, 1
for e in range(96): ind[x] = e; x = (x * 5) % 97
regen = [0] + [ind[v] % 3 for v in range(1, 97)]
gap97 = all(len({p[(b + i * 97) % 97] for i in range(4)}) == 1 for b in range(97))
report(bad == 0 and regen == p and gap97, "kappa_sum(4,3) = 96 (period-97 power residues)",
       f"9312 APs mono={bad} ==ind_5 mod 3:{regen == p} ceiling exact:{gap97}")

# ---------- 11-12: the mod-13 bracket palettes ----------
for fname, offs, lbl in [("bracket12_33_mod13.txt", (0, 5, 7), "HJ^[12](3,3) = inf (omega=(0,5,7) mod 13)"),
                         ("bracket12_42_mod13.txt", (0, 2, 3, 5), "HJ^[12](4,2) = inf (omega=(0,2,3,5) mod 13)")]:
    pal = read_palette(os.path.join(CERT, fname))
    bad = sum(1 for b in range(13) for k in range(1, 13)
              if len({pal[(b + o * k) % 13] for o in offs}) == 1)
    sharp = any(len({pal[(b + o * 13) % 13] for o in offs}) == 1 for b in range(13))
    report(bad == 0 and sharp, lbl, f"pairs=156 mono={bad} sharp at k=13:{sharp}")

# ---------- 13-15: the [3]^4 witnesses ----------
words4, L4 = grid_lines(3, 4); assert len(L4) == 175
col = read_grid(os.path.join(CERT, "hj1_3_witness_n4.txt"), 4)
IL = [l for l in L4 if (lambda a: a == list(range(a[0], a[-1] + 1)))(
      [i for i in range(4) if len({w[i] for w in l}) > 1])]
mono = sum(1 for l in IL if len({col[w] for w in l}) == 1)
report(mono == 0 and len(IL) == 142, "HJ^(1)(3) >= 5  ([3]^4 witness; = 5 with logs/)",
       f"interval lines={len(IL)} mono={mono}")

col = read_grid(os.path.join(CERT, "diagonal_only_n4.txt"), 4)
ml = [l for l in L4 if len({col[w] for w in l}) == 1]
okd = len(ml) == 1 and sorted(ml[0]) == [(1,1,1,1),(2,2,2,2),(3,3,3,3)]
report(okd, "diagonal-only [3]^4  => HJ^[3](3) >= 5", f"lines=175 mono=1 (the diagonal): {okd}")

col = read_grid(os.path.join(CERT, "ah34_ge25.txt"), 4)
rb = sum(1 for l in L4 if len({col[w] for w in l}) == 3)
report(rb == 0 and len(set(col.values())) == 24, "ah(3,4) >= 25  (rainbow-free 24-colouring)",
       f"lines=175 rainbow={rb} colours={len(set(col.values()))}")

# ---------- 16-17: unit-line witnesses ----------
def unit_check(t, n, fname):
    pts = list(itertools.product(range(t), repeat=n)); idx = {p: i for i, p in enumerate(pts)}
    chi = read_palette(os.path.join(CERT, fname)); assert len(chi) == len(pts)
    seen, bad, cnt = set(), 0, 0
    for v in itertools.product((0, 1), repeat=n):
        if not any(v): continue
        for a in pts:
            L = frozenset(tuple((a[i] + k * v[i]) % t for i in range(n)) for k in range(t))
            if L in seen: continue
            seen.add(L); cnt += 1
            if len({chi[idx[p]] for p in L}) == 1: bad += 1
    return bad, cnt
bad, cnt = unit_check(4, 4, "unit_42_n4.txt")
report(bad == 0 and cnt == 960, "HJunit(4,2) >= 5  (Z_4^4)", f"unit lines={cnt} mono={bad}")
bad, cnt = unit_check(5, 5, "unit_52_n5.txt")
report(bad == 0 and cnt == 19375, "HJunit(5,2) >= 6  (Z_5^5)", f"unit lines={cnt} mono={bad}")

# ---------- 18: level instance counts + degeneracy (Prop 5.2 / Sec 5.3) ----------
def monoid(m):
    return {2*a + 3*b + 5*c for a in range(m+1) for b in range(m+1) for c in range(m+1) if a+b+c <= m}
used = sorted(monoid(14))
homs = sorted({tuple(b + k * o for o in om) for k in range(1, 15) for b in monoid(14 - k)
               if b + 5 * k <= 70})
adj = {u: set() for u in used}
for H in homs:
    for a in H:
        adj[a].update(x for x in H if x != a)
edges = sum(len(v) for v in adj.values()) // 2
live = {u: set(v) for u, v in adj.items()}; deg = 0
while live:
    u = min(live, key=lambda x: len(live[x])); deg = max(deg, len(live[u]))
    for w in live[u]: live[w].discard(u)
    del live[u]
okL = (len(used) == 69 and sorted(set(range(71)) - set(used)) == [1, 69]
       and len(homs) == 443 and edges == 1386 and deg == 32)
report(okL, "Level instance I_(0,2,3,5),14 (Prop 5.2; unsat: logs/)",
       f"levels=69 (missing 1,69) homothets={len(homs)} edges={edges} degeneracy={deg}")

# ---------- 19-21: data files: censuses, Z_3^2, Prop 7.16 boundary ----------
try:
    sys.path.insert(0, os.path.join(HERE, "src"))
    from census_3cube import linefree, diagonal_only, strata, sumtype_count
    lf = linefree(); st, orb = strata(lf)
    j = json.load(open(os.path.join(DATA, "census_3cube_linefree.json")))
    ok = (len(lf) == 1644 == j["total"] and st == {"symmetric": 36, "C2": 504, "C3": 24, "trivial": 1080}
          and orb == 396 and sumtype_count(lf) == 16)
    report(ok, "Census: 1644 line-free 2-colourings of [3]^3 (Table A.5)",
           f"strata sym/C2/C3/triv = 36/504/24/1080, orbits 396, sum-type 16")
    do = diagonal_only(); st2, orb2 = strata(do)
    j2 = json.load(open(os.path.join(DATA, "census_3cube_diagonly.json")))
    ok = (len(do) == 6456 == j2["total"] and st2 == {"symmetric": 34, "C2": 1338, "C3": 8, "trivial": 5076}
          and orb2 == 1330 and sumtype_count(do) == 14)
    report(ok, "Census: 6456 diagonal-only 2-colourings of [3]^3 (Table A.6)",
           f"strata 34/1338/8/5076, orbits 1330, sum-type 14")
except Exception as e:
    report(False, "censuses", f"error: {e}")

pts2 = list(itertools.product(range(3), repeat=2)); i2 = {p: i for i, p in enumerate(pts2)}
seen, cyc = set(), []
for v in itertools.product(range(3), repeat=2):
    if v == (0, 0): continue
    for a in pts2:
        L = frozenset(tuple((a[i] + k * v[i]) % 3 for i in range(2)) for k in range(3))
        if L not in seen: seen.add(L); cyc.append([i2[p] for p in L])
mn, exact = 99, set()
for bits in range(512):
    colb = [(bits >> i) & 1 for i in range(9)]
    m = frozenset(j for j, L in enumerate(cyc) if len({colb[i] for i in L}) == 1)
    mn = min(mn, len(m))
    if len(m) == 2: exact.add(m)
report(mn == 2 and len(exact) == 66 and len(cyc) == 12,
       "Prop 7.9: Z_3^2 cyclic census (min forcing family = 11)",
       f"12 lines, min mono={mn}, exact pairs={len(exact)}/66")

T4 = cells(3, 4); ci = {c: i for i, c in enumerate(T4)}
tri = [tuple(ci[tuple(v[i] + (k if i == e else 0) for i in range(3))] for e in range(3))
       for k in range(1, 5) for v in cells(3, 4 - k)]
masks = set()
for bits in range(1 << 15):
    colb = [(bits >> i) & 1 for i in range(15)]
    m = 0
    for jx, T in enumerate(tri):
        if colb[T[0]] == colb[T[1]] == colb[T[2]]: m |= 1 << jx
    masks.add(m)
frc = lambda omit: not any((m & ~omit) == 0 for m in masks)
singles = [j for j in range(20) if frc(1 << j)]
doubles = sum(1 for a in range(20) for b in range(a + 1, 20) if frc((1 << a) | (1 << b)))
report(frc(0) and len(singles) == 4 and doubles == 0,
       "Prop 7.16: forcing boundary on T_4^(3) (four 19-triple minima)",
       f"20 triples; forcing single-omissions={len(singles)}, double-omissions={doubles}")

print("=" * 100)
if FAIL:
    print("FAILURES:", FAIL); sys.exit(1)
print("ALL CERTIFICATES AND DATA CLAIMS VERIFIED"); sys.exit(0)

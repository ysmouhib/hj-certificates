#!/usr/bin/env python3
"""Re-derives every certificate displayed in the paper, from the definitions.
Pure standard library; no solver, no dependency. Run: python3 verify_certificates.py

Note: the final census check enumerates all 2^27 two-colourings of [3]^3 and
takes a few minutes; every other check finishes in seconds."""

from itertools import product, permutations
from time import time

def mono(vals):            # is a pattern monochromatic?
    return len(set(vals)) == 1

def types(t, n):
    if t == 1: return [(n,)]
    return [(a,)+r for a in range(n+1) for r in types(t-1, n-a)]

fails = 0
def check(name, cond):
    global fails
    print(("PASS  " if cond else "FAIL  ") + name, flush=True)
    fails += (not cond)

# --- Theorem (HJ(3,3)>=16): length-76 interval certificate for S={0,2,5}, r=3
xi = ("1020111002012212220102011100201221221"
      "010201110020122122001020111002012212200")
xi = [int(c) for c in xi]
bad = sum(mono((xi[b], xi[b+2*k], xi[b+5*k]))
          for k in range(1, 16) for b in range(76 - 5*k))
check("length-76 certificate: no monochromatic homothet of {0,2,5}", len(xi)==76 and bad==0)

# --- Proposition (HJ(3,3)>=15): 49-periodic palette, weight (0,1,4), n=14
psi49 = [int(c) for c in "0112100212222001110021101201102002110220010200212"]
bad = sum(mono(tuple(psi49[(p+3*q+k*w) % 49] for w in (0,1,4)))
          for k in range(1,15) for p in range(15-k) for q in range(p+1))
check("49-cell periodic palette: line-free on [3]^14", bad==0)

# --- Theorem (HJ(4,2)>=14): period-26 palette, weight (0,2,3,5)
chi = [1,0,1,0,0,1,1,1,1,0,0,1,0,0,0,1,0,0,1,1,1,1,0,0,1,0]
def mono_quads(n):
    return sum(mono(tuple(chi[(2*v[1]+3*v[2]+5*v[3]+k*w) % 26] for w in (0,2,3,5)))
               for k in range(1,n+1) for v in types(4,n-k))
check("record palette: line-free on [4]^13", mono_quads(13)==0)
check("record palette: exactly 3 monochromatic quadruples at n=14", mono_quads(14)==3)

# --- Remark (anatomy): all-base check of the record palette mod 26
check("anatomy: all 26 bases bichromatic for every k<=12",
      all(not mono(tuple(chi[(b+k*w)%26] for w in (0,2,3,5)))
          for k in range(1,13) for b in range(26)))
check("anatomy: at k=13 exactly the bases {0,13} survive",
      sorted(b for b in range(26)
             if not mono(tuple(chi[(b+13*w)%26] for w in (0,2,3,5)))) == [0,13])

# --- Theorems (HJ^[12](3,3)=HJ^[12](4,2)=infinity): mod-13 palettes
p13 = [1,0,0,1,0,1,0,0,1,2,2,2,2]
check("HJ^[12](3,3) palette: 156 residue triples bichromatic",
      all(not mono((p13[b%13], p13[(b+5*k)%13], p13[(b+7*k)%13]))
          for b in range(13) for k in range(1,13)))
c13 = [1 if i in (4,5,7,9,11,12) else 0 for i in range(13)]
check("HJ^[12](4,2) palette: 156 residue quadruples bichromatic",
      all(not mono(tuple(c13[(b+k*w)%13] for w in (0,2,3,5)))
          for b in range(13) for k in range(1,13)))

# --- Proposition (ksum(3,3)=11): 12-periodic palette, gaps 1..11
g = [2,0,1,2,1,1,0,1,2,0,0,2]
check("ksum(3,3) palette: no monochromatic 3-AP of gap <= 11",
      all(not mono((g[b%12], g[(b+k)%12], g[(b+2*k)%12]))
          for b in range(12) for k in range(1,12)))

# --- Theorem (four colours) (i): window certificate for G_4({0,1,3}) >= 94
win = [int(c) for c in
       ("22130220111331203110033310220312022201201001113"
        "0130333223121021201113320210013312023023310331")]
bad = sum(mono((win[b], win[b+k], win[b+3*k]))
          for k in range(1, 31) for b in range(93 - 3*k))
check("window certificate: no monochromatic homothet {b,b+k,b+3k} in [0,92]",
      len(win) == 93 and bad == 0)

# --- Theorem (four colours) (ii): R_4(z+2x=3y) >= 59
rad = [int(c) for c in
       ("01021133302312200031321110222332"
        "03300021110313222001312333")]
bad = sum(mono((rad[b], rad[b+k], rad[b+3*k]))
          for k in range(1, 20) for b in range(58 - 3*k))
bad += sum(mono((rad[b], rad[b+2*k], rad[b+3*k]))
           for k in range(1, 20) for b in range(58 - 3*k))
check("solution-free certificate: no monochromatic injective solution of z+2x=3y",
      len(rad) == 58 and bad == 0)

# --- Appendix (SAT certificates): the new Gallai certificates of the
#     SAT program (Section "Computing Gallai and Rado numbers with SAT")
def homothets(S, N):
    out = set()
    for k in range(1, N):
        for b in range(N - k*max(S)):
            out.add(tuple(b + k*a for a in S))
    return out

def avoids(col, S):
    return all(len({col[c] for c in H}) > 1
               for H in homothets(S, len(col)))

SAT_CERTS_3 = [  # three colours
    ((0,1,5), 69,
     "000111222021020210121011100221220110010221101221021020012210212100202"),
    ((0,1,6), 81,
     "010112010202222101101100122021200012221000012211201221002120100120120201022212011"),
    ((0,1,7), 86,
     "01210000122221020111002002222110100220011210210221011202210102121100212012102121201010"),
    ((0,2,7), 86,
     "01211212012010002111100222201210020020212211011201002022221001102202011101202201011211"),
]
for S, n, s in SAT_CERTS_3:
    col = [int(c) for c in s]
    check(f"G_3({set(S)}) >= {n+1}: no monochromatic homothet in [0,{n-1}]",
          len(col) == n and avoids(col, S))

SAT_CERTS_2 = [  # two colours: set, cells (= G_2-1), string
    ((0,1,2,4), 37,
     "1011001010110101010010101011010011010"),
    ((0,1,3,4), 40,
     "0001100111010100001111000010101110011000"),
    ((0,2,4,5), 43,
     "0111110011101001000101100110100011111000011"),
    ((0,3,4,5), 43,
     "1000010101110001110000111100001111000011011"),
    ((0,1,4,5), 44,
     "00111110000011011001001101100100111110000011"),
    ((0,1,3,6), 51,
     "001111000111001010100101010100101011011000110000111"),
    ((0,2,3,6), 53,
     "00011110001110101101010001110110000101101011100011001"),
    ((0,1,2,6), 55,
     "0100110000111100001011100101110010110011011010001001001"),
    ((0,1,4,6), 57,
     "011100001111000111010010101010101101010101010010101011101"),
    ((0,1,2,7), 58,
     "0101110010011010001101100101101100101110010011010011000110"),
    ((0,2,5,7), 58,
     "0110001011110001110000101100110011000001111000111101000110"),
    ((0,1,3,7), 59,
     "00001101000011111000010110101101001001110010101110101101010"),
    ((0,2,4,7), 60,
     "011001111001100000011111110000001111001101001110010110000110"),
    ((0,1,4,7), 61,
     "0001011110101001001010110110100101001001010010101101010110100"),
    ((0,1,5,7), 61,
     "0001000110110010111101000101101000101101110010010010001111010"),
    ((0,2,3,7), 61,
     "0110111010010011011101001001101110000100110111000010011011100"),
    ((0,1,6,7), 78,
     "010111000101101110001001011100010110111000101101110001001011100010110111000101"),
    ((0,3,4,7), 78,
     "001000111010010001110100100011101101000111010010001110100100011101001000111010"),
]
for S, n, s in SAT_CERTS_2:
    col = [int(c) for c in s]
    check(f"G_2({set(S)}) = {n+1}: no monochromatic homothet in [0,{n-1}]",
          len(col) == n and avoids(col, S))

# --- Appendix (SAT certificates): the eight exact Rado certificates,
#     solution-free for z+kx=(k+1)y (both shapes {0,1,k+1} and {0,k,k+1})
SAT_CERTS_RADO = [  # k, r, cells (= R_r-1), string
    (2, 2, 12, "011001100110"),
    (3, 2, 16, "0101010110101010"),
    (4, 2, 18, "101001011001011010"),
    (5, 2, 24, "010101010101101010101010"),
    (2, 3, 28, "1010122102010211202020121201"),
    (3, 3, 53, "01220100102212122010010221212201001022121220100102210"),
    (4, 3, 54, "010221010221221010221010010221221010221010010221010221"),
    (5, 3, 59, "00102122102001021122020010122210100202211201001012212020010"),
]
for k, r, n, s in SAT_CERTS_RADO:
    col = [int(c) for c in s]
    check(f"R_{r}(z+{k}x={k+1}y) = {n+1}: solution-free on [0,{n-1}]",
          len(col) == n and avoids(col, (0, 1, k + 1))
          and avoids(col, (0, k, k + 1)))


# --- Corollary (power-residue instances): p=11 (t=4,r=2,g=2), p=97 (t=4,r=3,g=5),
#     p=37 (t=5,r=2,g=2), p=139 (t=6,r=2,g=2); all p(p-1) base-gap pairs
def power_residue_palette(p, r, g):
    ind, x = {}, 1
    for e in range(p - 1):
        ind[x] = e % r
        x = (x * g) % p
    return [0] + [ind[x] for x in range(1, p)]

for (p, r, t, g0) in [(11, 2, 4, 2), (97, 3, 4, 5), (37, 2, 5, 2), (139, 2, 6, 2)]:
    pr = power_residue_palette(p, r, g0)
    check(f"power-residue palette p={p} (t={t},r={r},g={g0}): "
          f"{p*(p-1)} base-gap pairs bichromatic",
          all(not mono(tuple(pr[(b + a*k) % p] for a in range(t)))
              for k in range(1, p) for b in range(p)))

# --- Theorem (HJ^(1)(3)=5): interval witness of [3]^4 (142 interval lines)
words = list(product((1, 2, 3), repeat=4))
A2 = [[1,1,0,1,0,0,0,1,1],[0,1,0,1,0,1,1,0,1],[1,0,1,0,1,1,0,1,0],
      [0,1,0,0,1,1,1,0,0],[1,0,1,0,1,1,0,1,0],[0,1,1,1,0,0,1,0,1],
      [1,0,1,1,0,0,0,1,1],[0,1,1,0,1,0,1,0,1],[0,1,0,0,1,1,1,0,0]]
pairs = list(product((1, 2, 3), repeat=2))
c_int = {p12 + p34: A2[i][j] for i, p12 in enumerate(pairs)
         for j, p34 in enumerate(pairs)}
def interval_lines(n, t=3):
    out = set()
    for i in range(n):
        for j in range(i, n):
            fixed = [q for q in range(n) if not i <= q <= j]
            for consts in product(range(1, t + 1), repeat=len(fixed)):
                line = []
                for a in range(1, t + 1):
                    w, ci = [], 0
                    for q in range(n):
                        if i <= q <= j:
                            w.append(a)
                        else:
                            w.append(consts[ci]); ci += 1
                    line.append(tuple(w))
                out.add(tuple(line))
    return out
lines4 = interval_lines(4)
check("interval witness: 142 lines of L^(1)([3]^4), none monochromatic",
      len(lines4) == 142 and
      all(not mono([c_int[w] for w in l]) for l in lines4))

# --- Conjecture (diagonal-only): [3]^4 witness, exactly one monochromatic line
A4 = [[0,1,0,1,1,0,0,0,1],[1,1,0,1,0,1,0,1,0],[0,0,1,0,1,0,1,0,1],
      [1,1,0,1,0,1,0,1,0],[1,0,1,0,0,1,1,1,0],[0,1,0,1,1,0,0,0,1],
      [0,0,1,0,1,0,1,0,1],[0,1,0,1,1,0,0,0,1],[1,0,1,0,0,1,1,1,0]]
c_diag = {p12 + p34: A4[i][j] for i, p12 in enumerate(pairs)
          for j, p34 in enumerate(pairs)}
def all_lines(n, t=3):
    out = set()
    for mask in range(1, 1 << n):
        fixed = [q for q in range(n) if not (mask >> q) & 1]
        for consts in product(range(1, t + 1), repeat=len(fixed)):
            line = []
            for a in range(1, t + 1):
                w, ci = [], 0
                for q in range(n):
                    if (mask >> q) & 1:
                        w.append(a)
                    else:
                        w.append(consts[ci]); ci += 1
                line.append(tuple(w))
            out.add(tuple(line))
    return out
lines_all = all_lines(4)
monolines = [l for l in lines_all if mono([c_diag[w] for w in l])]
check("diagonal-only witness: exactly one of the 175 lines of [3]^4 "
      "monochromatic, the diagonal",
      len(lines_all) == 175 and monolines ==
      [((1,1,1,1), (2,2,2,2), (3,3,3,3))])

# --- Census of [3]^3 (the table in Section 3) and the diagonal-only count
#     (Section 8): exhaustive enumeration of all 2^27 two-colourings of [3]^3.
#     This is the slow check: it runs a few minutes.
print("census: enumerating all 2^27 two-colourings of [3]^3 "
      "(this takes a few minutes) ...", flush=True)
_t0 = time()
words3 = list(product((0, 1, 2), repeat=3))
widx3 = {w: i for i, w in enumerate(words3)}
lines3 = set()
for _mask in range(1, 1 << 3):
    _fixed = [q for q in range(3) if not (_mask >> q) & 1]
    for _consts in product(range(3), repeat=len(_fixed)):
        _line = []
        for _a in range(3):
            _w, _ci = [], 0
            for _q in range(3):
                if (_mask >> _q) & 1:
                    _w.append(_a)
                else:
                    _w.append(_consts[_ci]); _ci += 1
            _line.append(widx3[tuple(_w)])
        lines3.add(tuple(sorted(_line)))
lmasks = []
for _L in lines3:
    _mm = 0
    for _c in _L:
        _mm |= 1 << _c
    lmasks.append(_mm)
dmask = (1 << widx3[(0,0,0)]) | (1 << widx3[(1,1,1)]) | (1 << widx3[(2,2,2)])
# coordinate permutations of S_3 acting on cell indices; True = transposition
perms3 = []
for _p in permutations(range(3)):
    if _p == (0, 1, 2):
        continue
    _act = [0]*27
    for _i, _w in enumerate(words3):
        _act[_i] = widx3[tuple(_w[_p[_q]] for _q in range(3))]
    perms3.append((_act, sum(_p[_q] == _q for _q in range(3)) == 1))
sig3 = [sum(_w) + 3 for _w in words3]   # letter-sum: letters are 1,2,3
fibers = {}
for _i, _s in enumerate(sig3):
    fibers.setdefault(_s, []).append(_i)

lf = diagonly = diagonly_sym = 0
stab = {"S3": 0, "C2": 0, "C3": 0, "triv": 0}
orbits = sym_lf = sumtype_lf = 0
for x in range(1 << 27):
    cnt = 0; isdiag = False
    for _mm in lmasks:
        _v = x & _mm
        if _v == 0 or _v == _mm:
            cnt += 1
            if _mm == dmask:
                isdiag = True
            if cnt == 2:
                break
    if cnt == 1:
        if isdiag:
            diagonly += 1
            _fix = 0
            for _act, _ in perms3:
                _ok = True
                for _i in range(27):
                    if ((x >> _i) & 1) != ((x >> _act[_i]) & 1):
                        _ok = False; break
                _fix += _ok
            if _fix == 5:
                diagonly_sym += 1
        continue
    if cnt == 2:
        continue
    # line-free colouring: stabilizer class, orbit representative, sum type
    lf += 1
    _fix = 0; _fixtrans = 0; _rep = x
    for _act, _istrans in perms3:
        _y = 0
        for _i in range(27):
            _y |= ((x >> _i) & 1) << _act[_i]
        if _y < _rep:
            _rep = _y
        if _y == x:
            _fix += 1
            _fixtrans += _istrans
    if _rep == x:
        orbits += 1
    if _fix == 5:
        stab["S3"] += 1
        sym_lf += 1
        if all(((x >> _f[0]) & 1) == ((x >> _i) & 1)
               for _f in fibers.values() for _i in _f[1:]):
            sumtype_lf += 1
    elif _fix == 1 and _fixtrans == 1:
        stab["C2"] += 1
    elif _fix == 2 and _fixtrans == 0:
        stab["C3"] += 1
    elif _fix == 0:
        stab["triv"] += 1
    else:
        stab["triv"] += 1  # unreachable; counted so the strata check fails loudly
print(f"census: enumeration done in {time()-_t0:.0f}s", flush=True)
check("census: 1644 line-free two-colourings of [3]^3", lf == 1644)
check("census: strata 36 symmetric / 504 C2 / 24 C3 / 1080 asymmetric",
      (stab["S3"], stab["C2"], stab["C3"], stab["triv"]) == (36, 504, 24, 1080))
check("census: 396 S_3-orbits of line-free colourings", orbits == 396)
check("census: 36 symmetric line-free, 16 of sum type",
      sym_lf == 36 and sumtype_lf == 16)
check("diagonal-only at n=3: exactly 6456 colourings with unique monochromatic "
      "line the diagonal, 34 of them symmetric",
      diagonly == 6456 and diagonly_sym == 34)

print("\n" + ("ALL CERTIFICATES VERIFIED" if fails==0 else f"{fails} CHECK(S) FAILED"))

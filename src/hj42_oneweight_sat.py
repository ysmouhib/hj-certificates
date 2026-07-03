"""
HJ(4,2) lower bounds via one-weight colorings + CryptoMiniSat.
One-weight:  c(w) = chi(<omega, type(w)> mod m),  omega in Z^4, chi: Z/m -> {0,1}.
Line-pattern lemma: c is line-free in [4]^n iff for every k in {1..n} and every
inactive type v (composition of n-k into 4 parts) the corner quadruple
chi(b+k*omega_1),...,chi(b+k*omega_4), b=<omega,v>, is NOT monochromatic.
Requires: pip install pycryptosat
"""
from pycryptosat import Solver
import time
 
def is_prime(x): return x >= 2 and all(x % d for d in range(2, int(x**.5)+1))
 
def comps_by_k(n):
    by = {}
    for k in range(1, n+1):
        s = n-k; L = []
        for v1 in range(s+1):
            for v2 in range(s-v1+1):
                for v3 in range(s-v1-v2+1):
                    L.append((v1, v2, v3, s-v1-v2-v3))
        by[k] = L
    return by
 
def line_free_sat(omega, m, n, COMP=None):
    """SAT model of: one-weight coloring (omega,m) is line-free in [4]^n."""
    if COMP is None: COMP = comps_by_k(n)
    s = Solver(); var = lambda p: p+1; o = omega
    for k in range(1, n+1):
        seen = set()
        for (v1, v2, v3, v4) in COMP[k]:
            b = (o[0]*v1+o[1]*v2+o[2]*v3+o[3]*v4) % m
            if b in seen: continue
            seen.add(b)
            pos = tuple(sorted({(b+k*o[j]) % m for j in range(4)}))
            if len(pos) == 1: return (False, None)          # collapses -> forced mono
            s.add_clause([var(p) for p in pos]); s.add_clause([-var(p) for p in pos])
    sat, sol = s.solve()
    return (sat, [1 if sol[var(p)] else 0 for p in range(m)] if sat else None)
 
def hjK_infinite_sat(omega, m, K):
    """SAT model of: one-weight coloring (omega,m) gives HJ^[K](4,2)=infinity."""
    s = Solver(); var = lambda p: p+1; o = omega
    for k in range(1, K+1):
        for S in range(m):
            pos = tuple(sorted({(S+k*o[j]) % m for j in range(4)}))
            if len(pos) == 1: return False
            s.add_clause([var(p) for p in pos]); s.add_clause([-var(p) for p in pos])
    return s.solve()[0]
 
def verify_line_free(omega, m, chi, n):
    for k in range(1, n+1):
        s = n-k
        for v1 in range(s+1):
            for v2 in range(s-v1+1):
                for v3 in range(s-v1-v2+1):
                    v4 = s-v1-v2-v3
                    b = (omega[0]*v1+omega[1]*v2+omega[2]*v3+omega[3]*v4) % m
                    if len({chi[(b+k*omega[j]) % m] for j in range(4)}) == 1:
                        return False, (k, (v1, v2, v3, v4))
    return True, None
 
if __name__ == "__main__":
    # 1. validate against the thesis closed form (Theorem hj42-14)
    omega, m = (0, 2, 3, 5), 26
    thesis = [1,0,1,0,0,1,1,1,1,0,0,1,0,0,0,1,0,0,1,1,1,1,0,0,1,0]
    print("1. (0,2,3,5), m=26:",
          "line-free n=13 =", verify_line_free(omega, m, thesis, 13)[0],
          "| n=14 =", verify_line_free(omega, m, thesis, 14)[0], "(sharp)")
    sat13, pal = line_free_sat(omega, m, 13)
    print("   SAT solves n=13 from scratch:", sat13, "=> HJ(4,2) >= 14")
 
    # 2. periodic one-weight ceiling: max K with HJ^[K](4,2)=inf
    bestK = 0
    for mm in range(5, 28):
        for a in range(1, mm):
            for b in range(a+1, mm):
                for c in range(b+1, mm):
                    K = min(mm-1, 14)
                    while K > bestK:
                        if hjK_infinite_sat((0, a, b, c), mm, K):
                            bestK = K; break
                        K -= 1
    print(f"2. periodic ceiling: max K with HJ^[K](4,2)=inf = {bestK} => HJ(4,2) >= {bestK+1}")
 
    # 3. n=14 (HJ(4,2)>=15) over one-weight: expect UNSAT everywhere
    COMP14 = comps_by_k(14); found = False; t0 = time.time()
    mods = sorted(set([2*p for p in range(7, 40) if is_prime(p)] + list(range(20, 46))))
    for mm in mods:
        for a in range(1, mm):
            for b in range(a+1, mm):
                for c in range(b+1, mm):
                    if line_free_sat((0, a, b, c), mm, 14, COMP14)[0]:
                        print("   SAT at n=14:", (0, a, b, c), mm); found = True
        if time.time()-t0 > 600: break
    print(f"3. line-free coloring in [4]^14 found? {found}")

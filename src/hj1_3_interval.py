import itertools
from pycryptosat import Solver          # pip install pycryptosat

T = 3                                   # alphabet [3]

# A line-free 2-coloring of [3]^4 (Table~\ref{tab:hj1-3-witness}), as a bit per
# word in the lexicographic order of itertools.product(range(1,4), repeat=4).
WITNESS_BITS = ("110100011010101101101011010010011100"
                "101011010011100101101100011011010101010011100")

def words(n):
    return list(itertools.product(range(1, T + 1), repeat=n))

def one_fold_lines(n):
    """Lines of L^{(1)}([3]^n): active coordinates form a single interval [i,j]."""
    for i in range(n):
        for j in range(i, n):
            inactive = [p for p in range(n) if p < i or p > j]
            for fixed in itertools.product(range(1, T + 1), repeat=len(inactive)):
                fx = dict(zip(inactive, fixed))
                yield tuple(tuple(fx[p] if p in fx else v for p in range(n))
                            for v in (1, 2, 3))

def avoidable(lines):
    """True iff some 2-coloring avoids a monochromatic member of `lines`."""
    verts = sorted({p for L in lines for p in L})
    var = {w: i + 1 for i, w in enumerate(verts)}
    s = Solver()
    for a, b, c in lines:
        x, y, z = var[a], var[b], var[c]
        s.add_clause([-x, -y, -z])      # not all color 1
        s.add_clause([x, y, z])         # not all color 0
    return s.solve()[0]

# ---- lower bound: verify the [3]^4 witness independently of the solver -----
color = {w: int(b) for w, b in zip(words(4), WITNESS_BITS)}
assert all(len({color[p] for p in L}) == 2 for L in one_fold_lines(4))
print("HJ^(1)(3) >= 5: [3]^4 witness has 0 monochromatic 1-fold lines")

# ---- upper bound: [3]^5 is UNSAT, extract a minimal forcing subfamily ------
L5 = list(one_fold_lines(5))
assert not avoidable(L5)                # no line-free coloring of [3]^5 exists
core, i = list(L5), 0
while i < len(core):                    # deletion-based minimization
    trial = core[:i] + core[i + 1:]
    if not avoidable(trial):
        core = trial                    # line i is redundant
    else:
        i += 1                          # line i is necessary
assert not avoidable(core)
assert all(avoidable(core[:k] + core[k + 1:]) for k in range(len(core)))
print(f"HJ^(1)(3) <= 5: forcing subfamily of {len(core)} lines verified minimal")
print("HJ^(1)(3) = 5")

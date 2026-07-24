#!/bin/sh
# drat_flagship.sh -- reproduce the DRAT-validated refutation of the flagship
# instance G_3({0,2,5}) at N = 77 from scratch.
# Requires: git, a C/C++ toolchain, python3. Runtime: ~10 min on one core.
set -e

# 1. Generate the CNF (independent 30-line encoder; clause-for-clause
#    identical to gallai_rado_sat.py's encoding, symmetry breaking included:
#    p cnf 231 2204).
python3 - <<'EOF'
S, r, N = (0, 2, 5), 3, 77
v = lambda c, i: c * r + i + 1
cls = []
for c in range(N):
    cls.append([v(c, i) for i in range(r)])
    for i in range(r):
        for j in range(i + 1, r):
            cls.append([-v(c, i), -v(c, j)])
m = max(S)
for k in range(1, (N - 1) // m + 1):
    for b in range(N - k * m):
        H = [b + k * s for s in S]
        for i in range(r):
            cls.append([-v(c, i) for c in H])
for i in range(r):                      # first-occurrence symmetry breaking
    for j in range(i + 1, r):
        for c in range(N):
            cls.append([-v(c, j)] + [v(cc, i) for cc in range(c)])
with open("flag77.cnf", "w") as f:
    f.write(f"p cnf {N*r} {len(cls)}\n")
    for c in cls:
        f.write(" ".join(map(str, c)) + " 0\n")
print(f"flag77.cnf written: {N*r} vars, {len(cls)} clauses")
EOF

# 2. Build solver and checker from source (skip if already present).
[ -x cadical/build/cadical ] || {
  git clone --depth 1 https://github.com/arminbiere/cadical
  ( cd cadical && ./configure && make -j2 )
}
[ -x drat-trim/drat-trim ] || {
  git clone --depth 1 https://github.com/marijnheule/drat-trim
  ( cd drat-trim && make )
}

# 3. Solve with proof logging (exit code 20 = UNSAT), then validate.
./cadical/build/cadical flag77.cnf flag77.drat || [ $? -eq 20 ]
./drat-trim/drat-trim flag77.cnf flag77.drat        # expect: s VERIFIED

# 4. Pin the artifact.
sha256sum flag77.cnf flag77.drat | tee flag77.sha256
xz -T0 -6 -k flag77.drat
ls -la flag77.drat flag77.drat.xz

# Session reference run (2026-07-24, CaDiCaL 3.0.1, single core):
#   solve+log ~8 min; proof 119,204,678 B; drat-trim "s VERIFIED" in 165.6 s;
#   1,457,406 / 2,021,700 lemmas in core; 36,158,882 resolution steps; 0 RAT.
#   sha256(flag77.drat) =
#   a3847f07afff404d778cf33698fdc120bca94d966dfdcbf3fdd32cf633d820eb
# Note: this certifies the symmetry-broken CNF; pair it with the paper's
# satisfiability-preservation remark, or rerun on the unbroken instance
# (drop the last clause block above; 1973 clauses, slower).

from hj_pipeline import *

# --- validation: UNSAT exactly at the known values -----------------
assert solve((2,), 2, 2)[0] is False      # HJ(2,2) = 2
assert solve((3,), 2, 3)[0] is False      # HJ(2,3) = 3
assert solve((4,), 3, 2)[0] is False      # HJ(3,2) = 4  (simplex)
assert solve((2, 2), 3, 2)[0] is False    # ... and 2-block quotients
assert solve((3, 1), 3, 2)[0] is False

# --- b = 1 is the simplex reduction: SAT instances below threshold --
res, m, _ = solve((17,), 3, 3)            # SAT: HJ(3,3) >= 18
assert res and verify_quotient((17,), 3, m) == 0
res, m, _ = solve((12,), 4, 2)            # SAT: HJ(4,2) >= 13
assert res and verify_quotient((12,), 4, m) == 0

# --- frontier: smallest enlargement of the symmetric class ---------
# Warm-start the (17,1) quotient at n = 18 from the n = 17 witness:
# the lift "ignore the new coordinate" violates only the lines whose
# active set meets it, so the solver starts near a solution.
cells, idx, _, _ = encode((17, 1), 3, 3)
phases = [idx[c] * 3 + m[(c[0],)] + 1 for c in cells]
res, model, _ = solve((17, 1), 3, 3, conf_budget=50_000_000,
                      phases=phases)
if res is None:                  # budget exhausted: split and retry
    status, model = cube_and_conquer((17, 1), 3, 3, depth=3,
                                     conf_budget=50_000_000)
if model is not None:
    assert verify_quotient((17, 1), 3, model) == 0   # => HJ(3,3) >= 19

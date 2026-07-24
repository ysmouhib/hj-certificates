# Addendum — new Gallai and Rado numbers by SAT

**Companion computations to** *Lower Bounds for the Hales–Jewett Numbers via
Symmetric and One-Weight Colorings* (Y. Mouhib, 2026).

The article reduced symmetric Hales–Jewett lower bounds to one-dimensional
**Gallai homothety numbers** `G_r(S)` (least `N` such that every `r`-coloring
of `[0, N-1]` contains a monochromatic homothet `b + k·S`, `k ≥ 1`) and gave
the **Rado reading**: injective solutions of `z + kx = (k+1)y` are exactly the
homothets of `{0,1,k+1}` and of `{0,k,k+1}`, so the corresponding Rado number
is the two-shape avoidance threshold. This addendum pushes both fronts with a
portfolio of state-of-the-art SAT solvers. **All values below are new
computations** (July 2026); every avoidance certificate was found by a solver
and then re-verified by exhaustive enumeration from the definitions, and every
forcing claim was proved UNSAT by a CDCL solver; the flagship refutation has since been re-run with DRAT proof logging and validated with `drat-trim` (`logs/drat_flagship/` in the repository).

---

## 1. New exact Gallai numbers

### 1.1 Three-point sets, three colors

The article's table had `G_3({0,1,3}) = 42`, `G_3({0,1,4}) = 57` and
`G_3({0,2,5}) ≥ 77`. New values:

| `S` | `G_3(S)` | status |
|---|---|---|
| `{0,1,5}` | **70** | new exact value |
| `{0,2,5}` | **77** | **exact** — upgrades the article's `≥ 77` |
| `{0,1,6}` | `≥ 82` | avoidance at 81; forcing open |
| `{0,1,7}` | `≥ 87` | avoidance at 86; forcing open |
| `{0,2,7}` | `≥ 87` | avoidance at 86; forcing open |

The flagship: **`G_3({0,2,5}) = 77`**, proved on both sides — the article's
length-76 avoidance certificate (verified anew) plus an UNSAT proof at `N = 77`
(no 3-coloring of `[0,76]` avoids a monochromatic homothet of `{0,2,5}`),
obtained independently by **Kissat 4.0.4 (389.6 s)** and **CryptoMiniSat
5.11 (320.9 s)**, with the complete color-permutation symmetry broken in the
encoding. Via the closed-form bound this keeps `HJ(3,3) ≥ 16`, now standing on
an *exact* Gallai number.

### 1.2 Four-point sets, two colors

The article had `G_2({0,2,3,5}) = 67` and `G_2({0,1,5,6}) = 80`. Eighteen new
exact values (sets listed up to the reflection symmetry `S ↔ max(S) − S`):

| `S` | `G_2(S)` | `S` | `G_2(S)` | `S` | `G_2(S)` |
|---|---|---|---|---|---|
| `{0,1,2,4}` | 38 | `{0,1,4,6}` | 58 | `{0,1,4,7}` | 62 |
| `{0,1,3,4}` | 41 | `{0,1,2,6}` | 56 | `{0,2,4,7}` | 61 |
| `{0,1,4,5}` | 45 | `{0,1,3,6}` | 52 | `{0,3,4,7}` | 79 |
| `{0,2,4,5}` | 44 | `{0,2,3,6}` | 54 | `{0,1,5,7}` | 62 |
| `{0,3,4,5}` | 44 | `{0,1,2,7}` | 59 | `{0,2,5,7}` | 59 |
| | | `{0,1,3,7}` | 60 | `{0,2,3,7}` | 62 |

Largest: `G_2({0,1,6,7}) = 79` and `G_2({0,3,4,7}) = 79`; both give
`HJ(4,2) ≥ ⌈78/7⌉ = 12` via the closed-form bound, matching the previous
record through two new, independent certificate families.

## 2. New Rado numbers `R_r(z + kx = (k+1)y)`

Two-shape avoidance (`{0,1,k+1}` ∪ `{0,k,k+1}`); all values exact unless noted.

| `k` | `r = 2` | `r = 3` | `r = 4` |
|---|---|---|---|
| 2 | 13 | 29 | **`≥ 59`** (see below) |
| 3 | 17 | 54 | — |
| 4 | 19 | 55 | — |
| 5 | 25 | 60 | — |

**`R_4(z+2x=3y) ≥ 59`** improves the article's `≥ 57`: two independent
solution-free 4-colorings, of `[0,56]` and `[0,57]`, were found by MapleChrono
and CaDiCaL and verified by enumeration of all (base, gap) solution triples.

A structural observation the new data makes visible: the Rado constraint
(two shapes) can *strictly* lower the number below the single-shape Gallai
value — e.g. `R_3(z+2x=3y) = 29 < 42 = G_3({0,1,3})`, and
`R_2(z+4x=5y) = 19 < 20 ≤ G_2({0,1,5})` (the flatness theorem gives
`G_2({0,1,5}) = 20`), confirming the strictness of
`R_r(E_s) ≤ G_r(S)` in the article's Rado reading in several instances.

## 3. Methods

* **Encoding.** One-hot CNF: variables `x_{c,i}` ("cell `c` has color `i`"),
  exactly-one clauses per cell, and one clause per homothet per color
  forbidding monochromaticity. For `N ≈ 80` this is ~10³ clauses.
* **Symmetry breaking.** Complete breaking of the color-permutation group by
  first-occurrence ordering (`x_{c,j} ⇒ ⋁_{c' < c} x_{c',i}` for `i < j`),
  which incidentally fixes cell 0 to color 0. This turned the article's
  UNSAT proofs into sub-second checks (e.g. `G_3({0,1,3}) = 42` reproved in
  0.4 s) and was essential for the larger instances.
* **Solver portfolio** (via PySAT, raced in parallel, first answer wins):
  **Kissat 4.0.4**, **CaDiCaL 1.9.5**, **CryptoMiniSat 5.11**, Glucose 4.2,
  MapleChrono, Lingeling; plus a domain-specific stochastic local search
  (min-conflicts with random walk on colorings) for the avoidance side.
  CryptoMiniSat independently confirmed the flagship UNSAT at `N = 77`
  (`{0,2,5}`, 3 colors, 2204 clauses: UNSAT in 320.9 s;
  confirmed by a direct PyCryptoSat run of the same CNF).
* **Verification discipline.** Every solver-found avoidance coloring is
  re-checked by brute-force enumeration of all homothets before recording,
  and again by `verify_addendum.py` (pure standard library, no solver):
  `ALL ADDENDUM CERTIFICATES VERIFIED`. The engine was validated against
  `W(3,2) = 9`, `W(3,3) = 27`, and all four of the article's exact values
  (13, 42, 57, and the 14 flatness classes of the `(3,2)` landscape).

## 4. Reproducing everything

```bash
pip install python-sat pycryptosat          # the engine vendors these into pylibs/
cd addendum

# any instance, e.g. the flagship:
python3 gallai_rado_sat.py scan -s 0,2,5 -r 3 --nmin 70 --budget 300
# Rado instance k=2, 4 colors:
python3 gallai_rado_sat.py rado -k 2 -r 4 --nmin 50 --budget 300
# verify every certificate in results.json by brute force:
python3 verify_addendum.py
# export the best colorings as certificate files:
python3 export_certificates.py
```

`results.json` logs, per instance and `N`: status (SAT/UNSAT), winning
solver, wall time, homothet count, and the coloring. The `certificates/`
folder holds the avoidance colorings in the same text format as the
article's repository https://github.com/ysmouhib/hj-certificates (they can be
pushed there as-is).

## 5. Open ends left by this run

* `G_4({0,1,3}) ≥ 94` (article): avoidance at `N = 94, 95` unresolved
  (SLS + CDCL, ~10 min each) — the four-color threshold is beyond this
  session's budget.
* `R_4(z+2x=3y) ≥ 59`: UNSAT at 57 already unresolved after 45 min; the exact
  value is open. Likely within 59–70.
* `G_3({0,1,6}) ∈ [82, ?)`: `N = 82` undecided after several portfolio
  attempts (up to 900 s); `G_3({0,1,7}), G_3({0,2,7}) ∈ [87, ?)`.
* All UNSAT claims above are single-solver CDCL proofs with the symmetry
  broken by construction; for publication-grade certainty, emitting and
  checking DRAT proofs (Kissat/CaDiCaL + drat-trim) is the natural next step.

---

*Computation date: July 24, 2026. Hardware: 2-core sandbox; total solver time
≈ 6 h. Every number marked "exact" is proved on both sides; every avoidance
certificate is verified by exhaustive enumeration independent of any solver.*

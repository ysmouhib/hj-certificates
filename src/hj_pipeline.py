"""
hj_pipeline.py -- Block-symmetric reduction for Hales-Jewett lower bounds.

Generalizes the simplex reduction (Lemma lem:sym-reduction of the thesis)
from the full symmetric group S_n to Young subgroups S_{n_1} x ... x S_{n_b}:

  * A coloring of [t]^n invariant under S_{n_1} x ... x S_{n_b} (permuting
    coordinates within each block) factors through the *block type map*
        w  |->  (type(w|B_1), ..., type(w|B_b))  in  T_{n_1} x ... x T_{n_b}.
  * A combinatorial line with k_i active coordinates in block i and
    inactive block types v_i is monochromatic under the lift iff the
    *block corner tuple*
        C = { (v_1 + k_1 e_a, ..., v_b + k_b e_a) : a in [t] }
    is monochromatic on the quotient.  (Same proof as lem:sym-reduction,
    blockwise; every (k_1..k_b, v_1..v_b) with sum k_i >= 1 is realized.)
  * b = 1 recovers the simplex reduction exactly; b = n the full cube.

A SAT witness on the quotient therefore certifies HJ(t,r) > n, verified by
a solver-independent check of all block corner tuples (verify_quotient).
"""
import time, random
from itertools import product
from math import comb
from pysat.solvers import Solver


# ---------- quotient cells and corner tuples -------------------------------

def types(n, t):
    """All type vectors (a_1..a_t), a_i>=0, sum=n."""
    if t == 1:
        return [(n,)]
    out = []
    def rec(prefix, rem, slots):
        if slots == 1:
            out.append(tuple(prefix) + (rem,)); return
        for a in range(rem + 1):
            rec(prefix + [a], rem - a, slots - 1)
    rec([], n, t)
    return out


def block_cells(blocks, t):
    """Cells of the quotient: tuples (v_1..v_b), v_i in T_{n_i}."""
    return [tuple(c) for c in product(*(types(ni, t) for ni in blocks))]


def block_corner_tuples(blocks, t):
    """All block corner tuples, each a tuple of t cells (one per letter)."""
    b = len(blocks)
    tuples_ = []
    for ks in product(*(range(ni + 1) for ni in blocks)):
        if sum(ks) == 0:
            continue
        for vs in product(*(types(blocks[i] - ks[i], t) for i in range(b))):
            cells = []
            for a in range(t):                      # letter a -> add k_i to entry a
                cell = tuple(tuple(vs[i][j] + (ks[i] if j == a else 0)
                                   for j in range(t)) for i in range(b))
                cells.append(cell)
            tuples_.append(tuple(cells))
    return tuples_


# ---------- encoding ---------------------------------------------------------

def encode(blocks, t, r):
    """Return (cells, cell_index, tuples, clauses). Variable id of (cell i,
    color j) is i*r+j+1 for r>=3; for r=2 one Boolean per cell (id i+1)."""
    cells = block_cells(blocks, t)
    idx = {c: i for i, c in enumerate(cells)}
    tuples_ = block_corner_tuples(blocks, t)
    clauses = []
    if r == 2:
        for tup in tuples_:
            ids = [idx[c] + 1 for c in tup]
            clauses.append(ids)                     # not all color 0
            clauses.append([-x for x in ids])       # not all color 1
        clauses.append([-1])                        # symmetry: cell 0 -> color 0
    else:
        vid = lambda i, j: i * r + j + 1
        for i in range(len(cells)):
            clauses.append([vid(i, j) for j in range(r)])   # at-least-one
        for tup in tuples_:
            ids = [idx[c] for c in tup]
            for j in range(r):
                clauses.append([-vid(i, j) for i in ids])
        clauses.append([vid(0, 0)])                 # symmetry: cell 0 -> color 0
    return cells, idx, tuples_, clauses


def star_degree_order(cells, idx, tuples_):
    """Cells sorted by descending 'star degree' = number of corner tuples
    through the cell (the quotient analogue of lambda(x) in Ch.4): these are
    the most constrained variables -- used for splitting/warm-start order."""
    deg = [0] * len(cells)
    for tup in tuples_:
        for c in tup:
            deg[idx[c]] += 1
    return sorted(range(len(cells)), key=lambda i: -deg[i]), deg


# ---------- solving ----------------------------------------------------------

def solve(blocks, t, r, solver='cadical195', conf_budget=None,
          phases=None, verbose=True):
    cells, idx, tuples_, clauses = encode(blocks, t, r)
    nvar = len(cells) if r == 2 else len(cells) * r
    if verbose:
        print(f"  blocks={blocks} t={t} r={r}: {len(cells)} cells, "
              f"{len(tuples_)} tuples, {nvar} vars, {len(clauses)} clauses")
    s = Solver(name=solver, bootstrap_with=clauses)
    if phases:
        s.set_phases(phases)
    t0 = time.time()
    if conf_budget:
        s.conf_budget(conf_budget)
        res = s.solve_limited()
    else:
        res = s.solve()
    dt = time.time() - t0
    model = None
    if res:
        m = set(s.get_model())
        if r == 2:
            model = {cells[i]: int(i + 1 in m) for i in range(len(cells))}
        else:
            model = {cells[i]: next(j for j in range(r) if i * r + j + 1 in m)
                     for i in range(len(cells))}
    s.delete()
    status = {True: 'SAT', False: 'UNSAT', None: 'UNKNOWN(budget)'}[res]
    if verbose:
        print(f"  -> {status}  ({dt:.1f}s)")
    return res, model, dt


# ---------- standalone verification (no solver involved) --------------------

def verify_quotient(blocks, t, model):
    """Exhaustively re-check every block corner tuple against the witness.
    Independent of the encoding: re-enumerates tuples from the definition."""
    bad = 0
    for tup in block_corner_tuples(blocks, t):
        if len({model[c] for c in tup}) == 1:
            bad += 1
    return bad


def lift_color(word, blocks, t, model):
    """Color of a word of [t]^n (letters 0..t-1) under the lifted coloring."""
    cell, pos = [], 0
    for ni in blocks:
        seg = word[pos:pos + ni]; pos += ni
        cell.append(tuple(seg.count(j) for j in range(t)))
    return model[tuple(cell)]


def sample_verify_cube(blocks, t, model, samples=200000, seed=0):
    """Sample random combinatorial lines of the full cube and check none is
    monochromatic under the lift -- a sanity check on top of the exhaustive
    quotient verification."""
    n = sum(blocks); rnd = random.Random(seed); bad = 0
    for _ in range(samples):
        k = rnd.randint(1, n)
        active = rnd.sample(range(n), k)
        base = [rnd.randrange(t) for _ in range(n)]
        cols = set()
        for a in range(t):
            w = list(base)
            for i in active:
                w[i] = a
            cols.add(lift_color(tuple(w), blocks, t, model))
        if len(cols) == 1:
            bad += 1
    return bad


# ---------- cube-and-conquer via star degrees (Chapter 4 -> Chapter 3) ------

def cube_and_conquer(blocks, t, r, depth=2, solver='cadical195',
                     conf_budget=2_000_000, verbose=True):
    """Split on the colors of the `depth` highest star-degree cells (the
    cells lying on the most corner tuples), solving each cube with a budget.
    Returns ('SAT', model) on the first satisfiable cube, 'UNSAT' if all
    cubes refuted, else 'UNKNOWN'. Color symmetry: the first split cell
    only needs colors 0..min over its orbit (we use 0..r-1 conservatively,
    except cell 0 which is pinned to color 0 by the encoding)."""
    cells, idx, tuples_, clauses = encode(blocks, t, r)
    order, deg = star_degree_order(cells, idx, tuples_)
    split = [i for i in order if i != 0][:depth]
    if verbose:
        print(f"  splitting on cells {[cells[i] for i in split]} "
              f"(star degrees {[deg[i] for i in split]})")
    vid = (lambda i, j: i + 1) if r == 2 else (lambda i, j: i * r + j + 1)
    from itertools import product as prod
    unknown = False
    for assign in prod(range(r), repeat=len(split)):
        s = Solver(name=solver, bootstrap_with=clauses)
        for i, j in zip(split, assign):
            if r == 2:
                s.add_clause([vid(i, 0) if j else -vid(i, 0)])
            else:
                s.add_clause([vid(i, j)])
        s.conf_budget(conf_budget)
        res = s.solve_limited()
        if verbose:
            print(f"    cube {assign}: "
                  f"{ {True:'SAT',False:'UNSAT',None:'?'}[res] }")
        if res:
            m = set(s.get_model())
            if r == 2:
                model = {cells[i]: int(i+1 in m) for i in range(len(cells))}
            else:
                model = {cells[i]: next(j for j in range(r) if i*r+j+1 in m)
                         for i in range(len(cells))}
            s.delete()
            return 'SAT', model
        if res is None:
            unknown = True
        s.delete()
    return ('UNKNOWN' if unknown else 'UNSAT'), None

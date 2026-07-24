#!/usr/bin/env python3
"""Export every best avoidance coloring in results.json to certificates/,
repo-style: one file per instance, with a header and the coloring string."""
import json, os, sys
sys.path.insert(0, '.')
from gallai_rado_sat import verify_coloring

res = json.load(open('results.json'))
os.makedirs('certificates', exist_ok=True)
manifest = []
for key, inst in sorted(res.items()):
    shapes = [tuple(map(int, s.split(','))) for s in key.split(':')[0].split('|')]
    r = int(key.split(':r')[1])
    sat = sorted((int(n) for n, v in inst.items() if v['status'] == 'SAT'))
    if not sat:
        continue
    n = max(sat)
    col = inst[str(n)]['coloring']
    assert verify_coloring(shapes, r, [int(x) for x in col])
    if len(shapes) == 1:
        S = shapes[0]
        name = f"gallai_{r}_{'_'.join(map(str, S))}_avoid_{n}.txt"
        desc = (f"# {r}-coloring of [0,{n - 1}] with no monochromatic "
                f"homothet of {list(S)}  =>  G_{r}({list(S)}) > {n}")
    else:
        k = shapes[0][2] - 1
        name = f"rado_{r}_z{k}x{k + 1}y_avoid_{n}.txt"
        desc = (f"# {r}-coloring of [0,{n - 1}] with no monochromatic "
                f"injective solution of z+{k}x={k + 1}y  =>  R_{r} > {n}")
    with open(os.path.join('certificates', name), 'w') as f:
        f.write(desc + "\n")
        f.write(f"# solver: {inst[str(n)].get('solver')}\n")
        f.write(col + "\n")
    manifest.append((name, n, desc[2:]))
    print("wrote", name)
json.dump(manifest, open('certificates/manifest.json', 'w'), indent=1)
print(len(manifest), "certificates exported")

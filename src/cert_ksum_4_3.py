# Period-97 power-residue 3-coloring; g=5 is a primitive root mod 97.
# CERTIFICATE chi : Z/97 -> {0,1,2}  (chi(0)=0):
CHI = ("0011212102220122120002021220010120021112110110002"
       "200011011211120021010022120200021221022201212110")   # length 97

p = 97
chi = lambda x: int(CHI[x % p])

# no monochromatic 4-AP of gap 1..96 (all 97*96 progressions) => kappa_sum(4,3) >= 96
bad = sum(1 for d in range(1, p) for a in range(p)
          if len({chi(a + i * d) for i in range(4)}) == 1)
assert bad == 0
print(f"gaps 1..96: {bad} monochromatic 4-APs  =>  kappa_sum(4,3) >= 96")

# sharpness: gap 97 collapses mod p and is forced monochromatic
assert any(len({chi(a + 97 * i) for i in range(4)}) == 1 for a in range(p))
print("gap 97: monochromatic (construction ceiling = 96)")

import cma
from math import sqrt

MULT = 1
ks = 0x391BC2164F0A*MULT
kr = 1.940035480806554e13*MULT
kR = 4.777053952827391e13*MULT

def radiusFit(s):
    v19 = ks*ks + s[0]*s[0] - s[1]*s[1]
    S_in = 4*ks*ks*s[0]*s[0] - v19*v19
    if S_in < 0:
        return float('inf')
    S = sqrt(S_in) / 4
    cr = 2*S / (ks + s[0] + s[1])
    cR = (ks*s[0]*s[1]) / (4*S)
    distr = (kr - cr)
    distR = (kR - cR)
    print(distr, distR)
    return abs(distr) + abs(distR)

es = cma.CMAEvolutionStrategy([70789268583970.951*MULT, 95523433899867.88*MULT], 0.2)
es.optimize(radiusFit, min_iterations=500)
print(es.result_pretty())
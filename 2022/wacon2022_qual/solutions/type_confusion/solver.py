#!/usr/bin/env python3

import angr, claripy

fn = './prob'

proj = angr.Project(fn)
state = proj.factory.entry_state(addr=0x400000+0x242F)

flag = claripy.BVS('flag', 64)
state.regs.rdx = flag
state.solver.add(flag != 0)

simulation = proj.factory.simgr(state)
simulation.explore(find=0x400000+0x244A, avoid=0x400000+0x24BC)

print(simulation.found[0].solver.eval(flag))

'''
from z3 import *

inp = BitVec('inp', 64)

comp = fpSignedToFP(RNE(), Extract(31, 0, inp), FloatDouble())
solve(And(inp!=0, comp == fpBVToFP(inp, FloatDouble())))
'''

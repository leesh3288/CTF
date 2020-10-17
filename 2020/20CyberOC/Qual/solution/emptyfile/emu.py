from z3 import *
from disasm import hyperop

class Op():
    def __init__(self, inst, ip, oplen, val=None):
        self.inst = inst
        self.ip = ip
        self.oplen = oplen
        self.val = val
    
    def __str__(self):
        s = "{:04x}: {}".format(self.ip, self.inst)
        if self.val is not None:
            if isinstance(self.val, Iterable):
                s += " " + " ".join("{:x}".format(v) for v in self.val)
            else:
                s += " {:x}".format(self.val)
        return s

def c2v(code, st):
    cur = 0
    val = 0
    while st + cur < len(code):
        if code[st + cur] == '\t':
            val = val * 2 + 1
        elif code[st + cur] == ' ':
            val = val * 2
        else:
            break
        cur += 1
    return val, st + cur + 1

s = Solver()
flag = BitVecs(' '.join('f{}'.format(i) for i in range(0x3a)), 32)

for f in flag:
    s.add(UGT(f, 0x20), ULT(f, 0x80))

ip = 0x131
sp = 0x3FFF
ctr = 0
while True:
    print("part {} @ ip {:x}".format(ctr, ip))

    ops = hyperop(ip)
    it = 0
    mem = [0] * 0x4000

    if ops[it].inst != 'WRITE_SUB':
        break  # complete  

    assert(ops[it].inst == 'WRITE_SUB')
    while ops[it].inst == 'WRITE_SUB':
        mem[int(ops[it].val[0][1:-1], 16)] = flag[int(ops[it].val[1][1:-1], 16)] - ops[it].val[2]  # symbol
        it += 1
    
    allowed = []
    assert(ops[it].inst == 'WRITE')
    while ops[it].inst == 'WRITE':
        idx, val = int(ops[it].val[0][1:-1], 16), ops[it].val[1]
        mem[idx] = val  # literal
        if val == 1:
            allowed.append(idx)
        it += 1
    
    write_pos = []
    assert(ops[it].inst == 'ASSERT_NZ_WRITE_Z')
    while ops[it].inst == 'ASSERT_NZ_WRITE_Z':
        base, deref = map(lambda x: int(x, 16), ops[it].val.replace('[', '').replace(']', '').replace('+', '').split())
        write_pos.append(base + mem[deref])
        it += 1
    
    for wpos in write_pos:
        cond = False
        for allow in allowed:
            cond = Or(cond, wpos == allow)
        s.add(cond)

    for i in range(len(write_pos) - 1):
        for j in range(i + 1, len(write_pos)):
            s.add(write_pos[i] != write_pos[j])

    must_write = []
    assert(ops[it].inst == 'ASSERT_N1')
    while ops[it].inst == 'ASSERT_N1':
        idx = int(ops[it].val[1:-1], 16)
        must_write.append(idx)
        it += 1
    
    for must in must_write:
        cond = False
        for wpos in write_pos:
            cond = Or(cond, must == wpos)
        s.add(cond)

    assert(ops[it].inst == 'NEQ_MULT_1_TO_12')
    while ops[it].inst == 'NEQ_MULT_1_TO_12':
        i1, i2 = int(ops[it].val[0][1:-1], 16), int(ops[it].val[1][1:-1], 16)
        for j in range(1, 12+1):
            s.add(mem[i1] != mem[i2] * j)
        it += 1

    assert(ops[it].inst == 'WRITE')
    while ops[it].inst == 'WRITE':
        it += 1
    
    assert(ops[it].inst == 'JMP')

    ip = ops[it].val

    print(s.check())
    model = s.model()
    flag_fin = bytearray(b"?"*0x3a)
    for i in range(len(flag)):
        f = flag[i]
        if model[f] is not None:
            flag_fin[i] = int(str(model[f]))
    print(flag_fin)

    ctr += 1

print("FLAG: " + flag_fin.decode('ascii'))
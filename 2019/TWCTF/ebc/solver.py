from z3 import *
import string

def unpack(p, l):
    assert(len(p) == l)
    return sum([(p[i] << (i * 8)) for i in range(l)])

def pack(u, l):
    p = ''
    for i in range(l):
        p += chr(u & 0xff)
        u >>= 8
    return p

def u64(p):
    return unpack(p, 8)

def p64(u):
    return pack(u, 8)

class CRC32:
    def __init__(self):
        self.table = []
        self.value = None

        for i in range(256):
            v = i
            for j in range(8):
                v = (0xEDB88320 ^ (v >> 1)) if(v & 1) == 1 else (v >> 1)
            self.table.append(v)

    def start(self):
        self.value = 0xffffffff

    def update(self, qword):
        for i in range(8):
            v = (self.value ^ (qword >> (i * 8) & 0xff)) & 0xFF
            for j in range(8):
                v =  If(v & 1 == 1, 0xEDB88320 ^ (v >> 1), v >> 1)
            self.value = v ^ (self.value >> 8)

    def finalize(self):
        return self.value ^ 0xffffffff

f = open('./input.ebc', 'rb').read()

z = BitVec('z', 64)
R = [0] * 8  # R0 ~ R7
R[1] = z

bans = []

s = Solver()
ite = 0
while ite < len(f):
    op = f[ite:ite+10]
    if op[0] == 0xf7 and op[1] & 0xf0 == 0x30:
        R[op[1] & 0xf] = u64(op[2:10])
        ite += 10
    elif op[0] == 0xb7 and op[1] & 0xf0 == 0x30:
        R[op[1] & 0xf] = unpack(op[2:6], 4)
        ite += 6
    elif op[0] == 0x77 and op[1] & 0xf0 == 0x30:
        R[op[1] & 0xf] = unpack(op[2:4], 2)
        ite += 4
    else:
        if op[0] == 0x20:
            R[op[1] & 0xf] = R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x4c:
            R[op[1] & 0xf] = R[op[1] & 0xf] + R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x4d:
            R[op[1] & 0xf] = R[op[1] & 0xf] - R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x4f:
            R[op[1] & 0xf] = R[op[1] & 0xf] * R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x56:
            R[op[1] & 0xf] = R[op[1] & 0xf] ^ R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x4a:
            R[op[1] & 0xf] = ~R[(op[1] & 0xf0) >> 4]
        elif op[0] == 0x4B:
            R[op[1] & 0xF] = -R[(op[1] >> 4) & 0xF]
        elif op[0] == 0x54:
            R[op[1] & 0xF] = R[op[1] & 0xF] & R[(op[1] >> 4) & 0xF]
        elif op[0] == 0x55:
            R[op[1] & 0xF] = R[op[1] & 0xF] | R[(op[1] >> 4) & 0xF]
        elif op[0] == 0x57:
            R[op[1] & 0xF] = (R[op[1] & 0xF] << R[(op[1] >> 4) & 0xF]) & 0xFFFFFFFFFFFFFFFF
        elif op[0] == 0x58:
            R[op[1] & 0xF] = LShR(R[op[1] & 0xF], R[(op[1] >> 4) & 0xF])
        elif op[0] == 0x45:
            s.add(R[op[1] & 0xF] == R[(op[1] >> 4) & 0xF])
            R[1] = BitVec('z2', 64)
            ite += 6
        else:
            print("Err : %x, %x"%(op[0], ite))
            exit(-1)
        ite += 2

crc32 = CRC32()
crc32.start()
crc32.update(z)
s.add(crc32.finalize() == 3242173371)

print(s.check())

m = s.model()
for d in m.decls():
    print("%s = %s" %(d.name(), m[d]))
    sol = m[d].as_long()
    s.add(z != sol)
    if False not in [c in string.printable for c in p64(sol)]:
        print(p64(sol))
        exit(0)

# TWCTF{EBC_1n7erpret3r_1s_m4d3_opt10n4l}


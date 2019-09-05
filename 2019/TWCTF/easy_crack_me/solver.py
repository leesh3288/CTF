#!/usr/bin/python3

from z3 import *

flag = [BitVec(str(i), 8) for i in range(39)]

rCount = [3, 2, 2, 0, 3, 2, 1, 3, 3, 1, 1, 3, 1, 2, 2, 3]
rAdd = [0x15e, 0x0da, 0x12f, 0x131, 0x100, 0x131, 0xfb, 0x102]
rXor = [0x52, 0x0c, 0x1, 0xf, 0x5c, 0x5, 0x53, 0x58]
rXor8 = [0x1, 0x57, 0x7, 0xd, 0xd, 0x53, 0x51, 0x51]
rAdd8 = [0x129, 0x103, 0x12b, 0x131, 0x135, 0x10b, 0xff, 0xff]
rType = [0x80, 0x80, 0xff, 0x80, 0xff, 0xff, 0xff, 0xff, 0x80 ,0xff, 0xff, 0x80, 0x80, 0xff, 0xff, 0x80, 0xff, 0xff, 0x80 ,0xff, 0x80, 0x80, 0xff, 0xff, 0xff, 0xff, 0x80, 0xff, 0xff, 0xff, 0x80, 0xff]

s = Solver()

s.add(flag[0] == ord('T'))
s.add(flag[1] == ord('W'))
s.add(flag[2] == ord('C'))
s.add(flag[3] == ord('T'))
s.add(flag[4] == ord('F'))
s.add(flag[5] == ord('{'))
s.add(flag[38] == ord('}'))

hexDigit = '0123456789abcdef'
for i in range(len(hexDigit)):
    s.add(Sum([If(fc == ord(hexDigit[i]), 1, 0) for fc in flag]) == rCount[i])

for i in range(8):
    add, xor, add8, xor8 = 0, 0, 0, 0  # temp
    for j in range(4):
        add += ZeroExt(8, flag[4*i+6+j])
        xor ^= flag[4*i+6+j]
        add8 += ZeroExt(8, flag[8*j+6+i])
        xor8 ^= flag[8*j+6+i]
    s.add(rAdd[i] == add)
    s.add(rXor[i] == xor)
    s.add(rAdd8[i] == add8)
    s.add(rXor8[i] == xor8)

for i in range(len(rType)):
    if rType[i] == 0x80:
        s.add(flag[i+6] >= ord('a'))
        s.add(flag[i+6] <= ord('f'))
    else:  # 0xff
        s.add(flag[i+6] >= ord('0'))
        s.add(flag[i+6] <= ord('9'))

s.add(Sum([ZeroExt(8, flag[2*(i+3)]) for i in range(16)]) == 0x488)

s.add(flag[37] == 53)
s.add(flag[7] == 102)
s.add(flag[11] == 56)
s.add(flag[12] == 55)
s.add(flag[23] == 50)
s.add(flag[31] == 52)

if s.check() == sat:
    m = s.model()
    for fc in flag:
        print(chr(m.evaluate(fc).as_long()), end='')
    print('')
    
# TWCTF{df2b4877e71bd91c02f8ef6004b584a5}

